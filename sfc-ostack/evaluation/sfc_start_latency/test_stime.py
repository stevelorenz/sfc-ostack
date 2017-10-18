#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: SFC start time measurements

       Use payload modification(pm) mode of ./st_timer.py

       - Before SFC creation: start with b'a'
       - After SFC creation: start with b'b'

Email: xianglinks@gmail.com
"""

import argparse
import os
import subprocess
import sys
sys.path.insert(0, '../')
import time

import paramiko
from openstack import connection

from sfc_mgr import EvaSFCMgr


def _get_floating_ip(pt_name):
    ins_port = conn.network.find_port(pt_name)
    fip = list(conn.network.ips(port_id=ins_port.id))[0].floating_ip_address
    return fip


def _ssh_cmd(ip, port, user, ssh_key, cmd):
    ssh_clt = paramiko.SSHClient()
    ssh_clt.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    while True:
        try:
            ssh_clt.connect(ip, port, user,
                            key_filename=ssh_key)
        except Exception:
            time.sleep(3)
        else:
            print('[DEBUG] Connect to instance succeeded.')
            break
    tran = ssh_clt.get_transport()
    for i in range(3):
        channel = tran.open_session()
        channel.exec_command(cmd)
        status = channel.recv_exit_status()
        print('[DEBUG] Command status: %d' % status)
        time.sleep(3)
    ssh_clt.close()


def test_sfc_ct(mode=0):
    """Test chain start time"""
    print('[TEST] Test SFC start time with python forwarding.')

    for srv_num in range(MIN_SF_NUM, MAX_SF_NUM + 1):
        ts_out_file = 'sfc-ts-ins-%d-%d.csv' % (mode, srv_num)
        CRT_RUN_CTIMER = RUN_CTIMER
        CRT_RUN_CTIMER += '-o %s ' % ts_out_file
        CRT_RUN_CTIMER += '-l ERROR > /dev/null 2>&1 &'
        print('[DEBUG] Cmd for running CTimer: %s' % CRT_RUN_CTIMER)
        # Run timer on the dst instance
        _ssh_cmd(DST_FIP, 22, SSH_USER, SSH_PKEY, CRT_RUN_CTIMER)
        time.sleep(3)

        print('[DEBUG] Start creating and deleting SFC')
        eva_sfc_mgr = EvaSFCMgr(SFC_CONF, INIT_SCRIPT)

        if mode == 0:
            print('[TEST] Run tests in mode 0.')
            # Chain start time stamp
            start_ts_file = 'sfc-ts-ctl-%d.csv' % srv_num
            ccts_lst = list()
            for round_num in range(1, TEST_ROUND + 1 + ADD_ROUND):
                print('[DEBUG] Test round: %d' % round_num)
                time.sleep(3)  # recv some A packets
                # Start ts of SFC start
                ccts_lst.append(time.time())
                srv_chain = eva_sfc_mgr.create_sc(srv_num, sf_wait_time=None)
                port_chain = eva_sfc_mgr.create_pc(srv_chain)
                time.sleep(15 * srv_num)  # recv some B packets
                # import ipdb
                # ipdb.set_trace()
                eva_sfc_mgr.delete_pc(port_chain)
                eva_sfc_mgr.delete_sc(srv_chain)
                time.sleep(3)

        if mode == 1:
            # TODO: should test after implementaion of SF manager
            pass
            # print('[TEST] Run tests in mode 1.')
            # srv_chain = eva_sfc_mgr.create_sc(srv_num, sf_wait_time=15)
            # for round_num in range(1, TEST_ROUND + 1 + ADD_ROUND):
            #     print('[DEBUG] Test round: %d' % round_num)
            #     time.sleep(10)  # recv some A packets
            #     # Create the port chain
            #     port_chain = eva_sfc_mgr.create_pc(srv_chain)
            #     time.sleep(10)  # recv some B packets
            #     # Delete the port chain
            #     eva_sfc_mgr.delete_pc(port_chain)
            #     time.sleep(3)
            # time.sleep(3)

            # eva_sfc_mgr.delete_sc(srv_chain)

        with open(start_ts_file, 'w+') as csv_f:
            for ts in ccts_lst:
                csv_f.write('%f\n' % ts)

        # Kill timer on dst instance
        _ssh_cmd(DST_FIP, 22, SSH_USER, SSH_PKEY, KILL_CTIMER)
        time.sleep(3)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description='Run SFC start time test.')
    ap.add_argument('min_sf', type=int, help='Minimal number of SF server')
    ap.add_argument('max_sf', type=int, help='Maximal number of SF server')
    ap.add_argument('-r', '--round', type=int, default=1,
                    help='Number of rounds for testing')
    ap.add_argument('--add_round', type=int, default=1,
                    help='Additional round for testing')
    ap.add_argument('-m', '--mode', type=int, choices=[0, 1], default=0,
                    help=('Measure mode.'
                          '0: Without checking for SF status.'
                          '1: With checking for SF status, smaller Gap-time')
                    )

    ap.add_argument('dst_addr', metavar='IP:PORT',
                    help='Fixed IP and port of the dst instance')
    ap.add_argument('dst_fip', help='Floating IP of the dst instance')

    ap.add_argument('--clean', help='Clear created SFC resources, used for tests',
                    action='store_true')
    ap.add_argument('--full_clean',
                    help='Also kill ctime_timer process on dst instance',
                    action='store_true')
    # ap.add_argument('--debug', help='Run in debug mode...',
    #                 action='store_true')

    if len(sys.argv) == 1:
        ap.print_help()
        sys.exit()
    args = ap.parse_args()

    auth_args = {
        'auth_url': 'http://192.168.100.1/identity/v3',
        'project_name': 'admin',
        'user_domain_name': 'default',
        'project_domain_name': 'default',
        'username': 'admin',
        'password': 'stack',
    }
    # Connection to the Ostack
    conn = connection.Connection(**auth_args)

    MIN_SF_NUM = args.min_sf
    MAX_SF_NUM = args.max_sf
    DST_ADDR = args.dst_addr
    DST_FIP = args.dst_fip
    TEST_ROUND = args.round
    ADD_ROUND = args.add_round

    SSH_USER = 'ubuntu'
    SFC_CONF = './sfc_conf.yaml'
    SSH_PKEY = '/home/zuo/sfc_ostack_test/sfc_test.pem'
    INIT_SCRIPT = './init_py_forwarding.sh'

    # Command to run and kill ctime_timer.py
    RUN_CTIMER = ''
    RUN_CTIMER += 'nohup python3 /home/ubuntu/ctime_timer.py '
    RUN_CTIMER += '-s %s ' % (DST_ADDR)
    RUN_CTIMER += '-m pm '
    RUN_CTIMER += '-r %s ' % TEST_ROUND
    KILL_CTIMER = "pkill -f 'python3 /home/ubuntu/ctime_timer.py'"

    # Command to run python forwarder
    RUN_FWD = ''
    RUN_FWD += 'nohup python3 /home/ubuntu/forwarder.py '
    RUN_FWD += '%s ' % DST_ADDR
    RUN_FWD += '> /dev/null 2>&1 &'
    print('[DEBUG] Cmd to run forwarder: %s' % RUN_FWD)

    # Try to cleanup all old resouces
    if args.clean or args.full_clean:
        print('[INFO] Run clean func')
        for srv_num in range(MIN_SF_NUM, MAX_SF_NUM + 1):
            try:
                subprocess.run(
                    ['python3', '../sfc_mgr.py', SFC_CONF,
                        INIT_SCRIPT, 'delete', '%d' % srv_num],
                    check=True)
            except Exception:
                pass
            if args.full_clean:
                print('[INFO] Run full clean func')
                _ssh_cmd(DST_FIP, 22, SSH_USER, SSH_PKEY, KILL_CTIMER)
            sys.exit(0)

    print('[DEBUG] Dst addr: %s, Dst floating IP:%s' % (DST_ADDR, DST_FIP))

    test_sfc_ct(args.mode)
