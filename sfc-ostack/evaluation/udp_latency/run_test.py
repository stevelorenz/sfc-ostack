#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Run UDP latency measurements

Email: xianglinks@gmail.com
"""

import argparse
import os
import subprocess
import sys
import time

import paramiko
from openstack import connection

from sfcostack import conf, log
from sfcostack.sfc import manager

if __name__ == "__main__":

    ap = argparse.ArgumentParser(description='Run UDP RTT latency test.')
    ap.add_argument('profile', help='To be tested profile')
    ap.add_argument('conf_file', help='sfc-ostack conf file')
    ap.add_argument('min_sf', help='Minimal number of SF servers')
    ap.add_argument('max_sf', help='Maximal number of SF servers')
    ap.add_argument('alloc_method', help='SFC allocation method')
    ap.add_argument('chain_method', help='SFC chain method')
    ap.add_argument('proxy_fip', help='Floating IP of proxy instance')
    ap.add_argument('pvt_key_file', help='SSH private key file')

    ap.add_argument('--n_packets', default=5000, type=int,
                    help='Number of sent packets for RTT testing')
    ap.add_argument('--min_round', default=1, type=int,
                    help='Minimal test round')
    ap.add_argument('--max_round', default=1, type=int,
                    help='Maximal test round')
    # ap.add_argument('-t', '--timeout', default=300, type=int,
    # help='Timeout if UDP client on the proxy has no response')
    ap.add_argument('-s', '--server', default='10.0.12.12:9999',
                    help='Address of UDP echo server')

    if len(sys.argv) == 1:
        ap.print_help()
        sys.exit()
    args = ap.parse_args()

    profile = args.profile
    conf_file = args.conf_file
    min_sf_num = int(args.min_sf)
    max_sf_num = int(args.max_sf)
    alloc_method = args.alloc_method
    chain_method = args.chain_method
    server_addr = args.server
    proxy_fip = args.proxy_fip
    pvt_key_file = args.pvt_key_file

    n_packets = args.n_packets
    send_rate = 128000
    payload_len = 512

    sfc_conf = conf.SFCConf()
    sfc_conf.load_file(conf_file)
    log.conf_logger(level=sfc_conf.log.level)

    sample_ins = sfc_conf.sample_server.copy()

    sfc_mgr = manager.StaticSFCManager(
        sfc_conf.auth,
        mgr_ip=sfc_conf.sfc_mgr_conf.mgr_ip,
        mgr_port=sfc_conf.sfc_mgr_conf.mgr_port
    )

    # SSH client for proxy instance
    proxy_ssh_clt = paramiko.SSHClient()
    proxy_ssh_clt.load_system_host_keys()
    proxy_ssh_clt.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    proxy_ssh_clt.connect(proxy_fip, port=22,
                          username='ubuntu', key_filename=pvt_key_file)
    print('Create SSH client to the proxy instance')

    kill_cmd = 'killall python3'

    for srv_num in range(min_sf_num, max_sf_num + 1):
        print('# Current server number: %d' % srv_num)
        sfc_conf.server_chain = list()
        for idx in range(srv_num):
            sample_ins['name'] = 'sf%d' % idx
            sfc_conf.server_chain.append([sample_ins.copy()])
        for rd in range(args.min_round, args.max_round + 1):
            print('# Current test round: %d' % rd)
            output_file = '-'.join(
                map(str, (profile, send_rate, payload_len, srv_num, rd))
            ) + '.csv'

            base_cmd = ''
            base_cmd += 'python3 /home/ubuntu/udp_latency.py -c %s --payload_len %s ' % (
                server_addr, payload_len)
            base_cmd += '--send_rate %s ' % (send_rate)
            base_cmd += '--output_file %s ' % (output_file)

            warm_up_cmd = base_cmd + '--n_packets 50 --clt_no_recv'
            test_cmd = base_cmd + '--n_packets %s' % n_packets

            # Create SFC
            sfc = sfc_mgr.create_sfc(sfc_conf, alloc_method,
                                     chain_method, wait_sf_ready=True)

            # Run warm ups
            for warm_rd in range(2):
                print('Run warm up')
                stdin, stdout, stderr = proxy_ssh_clt.exec_command(warm_up_cmd)
                print(stdout.read().decode())
            # Langsamer bitte...
            time.sleep(3)
            # Run RTT test
            print('Run RTT test')
            stdin, stdout, stderr = proxy_ssh_clt.exec_command(test_cmd)
            print(stdout.read().decode())

            time.sleep(3)

            sfc_mgr.delete_sfc(sfc)
