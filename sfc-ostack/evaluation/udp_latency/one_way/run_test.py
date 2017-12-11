#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: UDP one way delay measurements

Email: xianglinks@gmail.com
"""

import argparse
import os
import subprocess
import sys
import time

import paramiko

from sfcostack import conf, log
from sfcostack.sfc import manager


def _ssh_cmd(ip, port, user, ssh_key, cmd, exit_status=None):
    """Run command multiple times via SSH"""
    ssh_clt = paramiko.SSHClient()
    ssh_clt.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    while True:
        try:
            ssh_clt.connect(ip, port, user,
                            key_filename=ssh_key)
        except Exception:
            time.sleep(3)
        else:
            break
    tran = ssh_clt.get_transport()
    channel = tran.open_session()
    channel.exec_command(cmd)
    status = channel.recv_exit_status()
    if exit_status:
        if status != exit_status:
            raise RuntimeError('Run command:%s failed via SSH' % cmd)
    ssh_clt.close()


def run_test():
    """Test SFC start and gap time"""

    sfc_conf = conf.SFCConf()
    sfc_conf.load_file(CONF_FILE)
    log.conf_logger(level=sfc_conf.log.level)

    sample_ins = sfc_conf.sample_server.copy()

    sfc_mgr = manager.StaticSFCManager(
        sfc_conf.auth,
        mgr_ip=sfc_conf.sfc_mgr_conf.mgr_ip,
        mgr_port=sfc_conf.sfc_mgr_conf.mgr_port,
        return_ts=True
    )

    src_ssh_clt = paramiko.SSHClient()
    src_ssh_clt.load_system_host_keys()
    src_ssh_clt.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    src_ssh_clt.connect(SRC_FIP, port=22,
                        username='ubuntu', key_filename=PVT_KEY_FILE)

    print('[TEST] Run test with method: %s' % METHOD)
    for srv_num in range(MIN_SF_NUM, MAX_SF_NUM + 1):
        out_file = '%s-owd-%d.csv' % (METHOD, srv_num)
        CRT_RUN_TIMER_SRV = RUN_TIMER_SRV
        CRT_RUN_TIMER_SRV += '-o %s ' % out_file
        CRT_RUN_TIMER_SRV += '-l ERROR > /dev/null 2>&1 &'
        print('[DEBUG] Cmd for running RUN_TIMER_SRV: %s' % CRT_RUN_TIMER_SRV)

        print('[DEBUG] Current server number: %d' % srv_num)
        sfc_conf.server_chain = list()
        for idx in range(srv_num):
            sample_ins['name'] = 'sf%d' % idx
            sfc_conf.server_chain.append([sample_ins.copy()])

        print('[DEBUG] Start creating and deleting SFC %d times' % TEST_ROUND)

        for rd in range(1, TEST_ROUND + 1):
            print('[DEBUG] Current round: %d' % rd)
            sfc, _ = sfc_mgr.create_sfc(sfc_conf, ALLOC_METHOD,
                                        CHAIN_METHOD, wait_sf_ready=True)
            time.sleep(3)

            # Run warm up
            warm_up_cmd = RUN_TIMER_CLT + '--n_packets 50'
            for warm_rd in range(2):
                print('Run warm up!')
                stdin, stdout, stderr = src_ssh_clt.exec_command(warm_up_cmd)
                print(stdout.read().decode())
            time.sleep(3)

            # Run UDP server on dst instance
            _ssh_cmd(DST_FIP, 22, SSH_USER, PVT_KEY_FILE, CRT_RUN_TIMER_SRV,
                     exit_status=0)

            # Run UDP client on src instance
            test_cmd = RUN_TIMER_CLT + '--n_packets %s' % (N_PACKETS + 5)
            stdin, stdout, stderr = src_ssh_clt.exec_command(test_cmd)
            print(stdout.read().decode())
            time.sleep(3)

            # Kill timer on dst instance
            _ssh_cmd(DST_FIP, 22, SSH_USER, PVT_KEY_FILE, KILL_TIMER_SRV)
            time.sleep(3)

            sfc_mgr.delete_sfc(sfc)
            time.sleep(5)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description='Run SFC start and gap time tests.')

    ap.add_argument('method', type=str,
                    help='To be test SFC method. e.g. ns,fn,nsrd')
    ap.add_argument('conf_file', help='sfc-ostack conf file')
    ap.add_argument('alloc_method', help='SFC allocation method')
    ap.add_argument('chain_method', help='SFC chain method')
    ap.add_argument('min_sf', type=int, help='Minimal number of SF server')
    ap.add_argument('max_sf', type=int, help='Maximal number of SF server')

    ap.add_argument('dst_addr', metavar='IP:PORT',
                    help='Fixed IP and port of the dst instance')
    ap.add_argument('dst_fip', help='Floating IP of the dst instance')
    ap.add_argument('src_fip', help='Floating IP of the src instance')
    ap.add_argument('pvt_key_file', help='SSH private key file')

    ap.add_argument('-r', '--round', type=int, default=1,
                    help='Number of rounds for test')
    ap.add_argument('-n', '--n_packets', type=int, default=10,
                    help='Number of packets to be sent')

    if len(sys.argv) == 1:
        ap.print_help()
        sys.exit()

    args = ap.parse_args()

    METHOD = args.method
    CONF_FILE = args.conf_file
    MIN_SF_NUM = args.min_sf
    MAX_SF_NUM = args.max_sf
    ALLOC_METHOD = args.alloc_method
    CHAIN_METHOD = args.chain_method
    DST_ADDR = args.dst_addr
    DST_FIP = args.dst_fip
    SRC_FIP = args.src_fip
    TEST_ROUND = args.round
    N_PACKETS = args.n_packets
    SSH_USER = 'ubuntu'
    PVT_KEY_FILE = args.pvt_key_file

    RUN_TIMER_SRV = ''
    RUN_TIMER_SRV += 'nohup python3 /home/ubuntu/owd_timer.py -l ERROR '
    RUN_TIMER_SRV += '-s %s ' % (DST_ADDR)
    RUN_TIMER_SRV += '-n %s ' % (N_PACKETS)
    KILL_TIMER_SRV = "pkill -f 'python3 /home/ubuntu/owd_timer.py'"

    RUN_TIMER_CLT = ''
    RUN_TIMER_CLT += 'python3 /home/ubuntu/owd_timer.py -l ERROR '
    RUN_TIMER_CLT += '-c %s ' % (DST_ADDR)
    # 5 ms come from rtt tests
    RUN_TIMER_CLT += '--send_interval 0.005 '

    print('[DEBUG] Dst addr: %s, Dst floating IP:%s' % (DST_ADDR, DST_FIP))
    run_test()
