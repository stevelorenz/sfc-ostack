#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: SFC start and gap time measurements

       - Before SFC creation: start with b'a'
       - After SFC creation: start with b'b'

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

    print('[TEST] Run test with method: %s' % METHOD)
    for srv_num in range(MIN_SF_NUM, MAX_SF_NUM + 1):
        ts_out_file = '%s-sfc-ts-ins-%d.csv' % (METHOD, srv_num)
        CRT_RUN_GTIMER = RUN_GTIMER
        CRT_RUN_GTIMER += '-o %s ' % ts_out_file
        CRT_RUN_GTIMER += '-l ERROR > /dev/null 2>&1 &'
        print('[DEBUG] Cmd for running GTIMER: %s' % CRT_RUN_GTIMER)

        # Run gap timer on the dst instance
        _ssh_cmd(DST_FIP, 22, SSH_USER, PVT_KEY_FILE, CRT_RUN_GTIMER,
                 exit_status=0)
        time.sleep(3)

        print('[DEBUG] Current server number: %d' % srv_num)
        sfc_conf.server_chain = list()
        for idx in range(srv_num):
            sample_ins['name'] = 'sf%d' % idx
            sfc_conf.server_chain.append([sample_ins.copy()])

        print('[DEBUG] Start creating and deleting SFC %d times' % TEST_ROUND)

        ctl_ts_file = '%s-sfc-ts-ctl-%d.csv' % (METHOD, srv_num)
        ctl_ts_lst = list()

        for rd in range(1, TEST_ROUND + 1):
            sfc, time_info = sfc_mgr.create_sfc(sfc_conf, ALLOC_METHOD,
                                                CHAIN_METHOD, wait_sf_ready=True)
            ctl_ts_lst.append(time_info)
            time.sleep(5)

            sfc_mgr.delete_sfc(sfc)

        with open(ctl_ts_file, 'w+') as csv_f:
            for ts_tpl in ctl_ts_lst:
                csv_f.write(','.join(map(str, ts_tpl)))
                csv_f.write('\n')

        # Kill timer on dst instance
        _ssh_cmd(DST_FIP, 22, SSH_USER, PVT_KEY_FILE, KILL_GTIMER)
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
    ap.add_argument('pvt_key_file', help='SSH private key file')

    ap.add_argument('-r', '--round', type=int, default=1,
                    help='Number of rounds for testing')

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
    TEST_ROUND = args.round
    SSH_USER = 'ubuntu'
    PVT_KEY_FILE = args.pvt_key_file

    # Command to run and kill gap_timer.py
    RUN_GTIMER = ''
    RUN_GTIMER += 'nohup python3 /home/ubuntu/gap_timer.py '
    RUN_GTIMER += '-s %s ' % (DST_ADDR)
    RUN_GTIMER += '-r %s ' % TEST_ROUND

    KILL_GTIMER = "pkill -f 'python3 /home/ubuntu/gap_timer.py'"

    print('[DEBUG] Dst addr: %s, Dst floating IP:%s' % (DST_ADDR, DST_FIP))
    run_test()
