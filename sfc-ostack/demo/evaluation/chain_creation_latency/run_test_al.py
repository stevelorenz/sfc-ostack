#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Run SFC creation time measurements
       Based on maximal allowed latency(al)

Email: xianglinks@gmail.com
"""

import argparse
import os
import subprocess
import sys
import time

import paramiko


def lk_forwarding_test():
    print('[TEST] Test chain creation time with kernel forwarding')
    for srv_num in range(MIN_SF_NUM, MAX_SF_NUM + 1):
        outfile_name = 'cen-lkf-%d-cctime-al.csv' % srv_num
        CRT_RUN_CTIMER = RUN_CTIMER
        CRT_RUN_CTIMER += '-o %s ' % outfile_name
        CRT_RUN_CTIMER += '> /dev/null 2>&1 &'
        print('[DEBUG] Cmd for running CTimer: %s' % CRT_RUN_CTIMER)
        ssh_clt = paramiko.SSHClient()
        ssh_clt.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Run ctime_timer on recv instance
        while True:
            try:
                ssh_clt.connect(DST_FIP, 22, SSH_USER,
                                key_filename=SSH_PKEY)
            except Exception:
                print(
                    '[Error] Can not connect instance, try again after 3 seconds'
                )
                time.sleep(3)
            else:
                print('[DEBUG] Connect to instance succeeded.')
                break
        transport = ssh_clt.get_transport()
        for i in range(5):
            channel = transport.open_session()
            print('[DEBUG] Run ctime_timer on recv instance.')
            channel.exec_command(CRT_RUN_CTIMER)
            status = channel.recv_exit_status()
            print('[DEBUG] ctime_timer process status: %d' % status)
            time.sleep(3)
        ssh_clt.close()
        time.sleep(10)

        print('[DEBUG] Start creating and deleting SFC')
        for round_num in range(1, TEST_ROUND + 1):
            # Create and delete SFC
            subprocess.run(
                ['python3', '../sfc_mgr.py', SFC_CONF,
                    INIT_SCRIPT, 'create', '%d' % srv_num],
                check=True)
            time.sleep(60)
            subprocess.run(
                ['python3', '../sfc_mgr.py', SFC_CONF,
                    INIT_SCRIPT, 'delete', '%d' % srv_num],
                check=True)
            time.sleep(60)


def py_forwarding_test():
    pass


if __name__ == "__main__":

    ap = argparse.ArgumentParser(description='Run chain creation latency test')
    ap.add_argument('fw', help='Forwarding method',
                    choices=['kernel', 'python'])
    ap.add_argument('min_sf', type=int, help='Minimal number of SF server')
    ap.add_argument('max_sf', type=int, help='Maximal number of SF server')
    ap.add_argument('test_round', type=int, help='Number of test rounds')

    ap.add_argument('--dst_ip', type=str, default='127.0.0.1',
                    help='Fixed IP of the dst instance')
    ap.add_argument('--port', type=int, default=9999,
                    help='Listening port of the dst instance')
    ap.add_argument('-d', '--max_delay', type=float, default=0.005,
                    help='Maximal allowed recv delay, default 0.005 second')
    ap.add_argument('--dst_fip', type=str,
                    help='Floating IP of the dst instance')

    if len(sys.argv) == 1:
        ap.print_help()
        sys.exit()
    args = ap.parse_args()

    MIN_SF_NUM = args.min_sf
    MAX_SF_NUM = args.max_sf
    TEST_ROUND = args.test_round
    # MARK: Used for SSH
    DST_FIP = args.dst_fip
    MAX_ALLOWED_DELAY = args.max_delay

    # Command to run and kill ctime_timer.py
    RUN_CTIMER = ''
    RUN_CTIMER += 'nohup python3 /home/ubuntu/ctime_timer.py '
    RUN_CTIMER += '-s %s:%s ' % (args.dst_ip, args.port)
    RUN_CTIMER += '-m al '
    RUN_CTIMER += '-d %s ' % MAX_ALLOWED_DELAY
    # MARK: create and delete SHOULD have 2 times long delay
    RUN_CTIMER += '-r %s ' % int(args.test_round * 2)

    KILL_CTIMER = "pkill -f 'nohup python3 /home/ubuntu/ctime_timer.py'"

    # print(RUN_CTIMER)
    # print(KILL_CTIMER)

    SFC_CONF = './sfc_conf.yaml'
    SSH_USER = 'ubuntu'
    SSH_PKEY = '/home/zuo/sfc_ostack_test/sfc_test.pem'

    if args.fw == 'python':
        INIT_SCRIPT = './init_py_forwarding.sh'
        py_forwarding_test()
    elif args.fw == 'kernel':
        INIT_SCRIPT = './init_lk_forwarding.sh'
        lk_forwarding_test()
