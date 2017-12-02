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

from sfcostack import conf
from sfcostack.sfc import manager


def _ssh_cmd(ip, port, user, ssh_key, cmd):
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


def run_test(method):
    """Test SFC start and gap time"""
    print('[TEST]')
    for srv_num in range(MIN_SF_NUM, MAX_SF_NUM + 1):
        ts_out_file = '%s-sfc-ts-ins-%d.csv' % (method, srv_num)
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
            ctl_ts_lst = list()
            for round_num in range(1, TEST_ROUND + 1 + ADD_ROUND):
                print('[DEBUG] Test round: %d' % round_num)
                time.sleep(3)  # recv some A packets
                srv_chn_start = time.time()
                srv_chain = eva_sfc_mgr.create_sc(srv_num, sf_wait_time=None)
                srv_chn_end = time.time()
                port_chain = eva_sfc_mgr.create_pc(srv_chain)
                port_chn_end = time.time()
                time.sleep(30 * srv_num)  # recv some B packets
                # import ipdb
                # ipdb.set_trace()
                eva_sfc_mgr.delete_pc(port_chain)
                eva_sfc_mgr.delete_sc(srv_chain)
                time.sleep(3)
                ctl_ts_lst.append((srv_chn_start, srv_chn_end, port_chn_end))

        # TODO(zuo): Remove usage of eva_sfc_mgr
        if mode == 1:
            EVA_SERVER = {
                'image': 'ubuntu-cloud',
                'flavor': 'sfc_test',
                'init_script': './init_py_forwarding.sh',
                'ssh': {
                    'user_name': 'ubuntu',
                    'pub_key_name': 'sfc_test',
                    'pvt_key_file': '/home/zuo/sfc_ostack_test/sfc_test.pem'
                }
            }
            print('[TEST] Run tests in mode 1 with SFC StaicManager.')
            sfc_mgr = manager.StaticSFCManager(mgr_ip='192.168.100.1')
            import ipdb
            ipdb.set_trace()
            sfc_conf = conf.SFCConf(eva_sfc_mgr.conf_hd.conf_dict)
            for idx in range(1, srv_num + 1):
                cur_srv = EVA_SERVER.copy()
                cur_srv.update(
                    {'name': 'chn%s' % srv_num, }
                )
                sfc_conf.append_srv_grp([cur_srv])
            sfc = sfc_mgr.create_sfc(sfc_conf)
            sfc_mgr.delete_sfc(sfc)

        with open(start_ts_file, 'w+') as csv_f:
            for ts_tpl in ctl_ts_lst:
                csv_f.write(','.join(map(str, ts_tpl)))
                csv_f.write('\n')

        # Kill timer on dst instance
        _ssh_cmd(DST_FIP, 22, SSH_USER, SSH_PKEY, KILL_CTIMER)
        time.sleep(3)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description='Run SFC start and gap time tests.')

    ap.add_argument('min_sf', type=int, help='Minimal number of SF server')
    ap.add_argument('max_sf', type=int, help='Maximal number of SF server')
    ap.add_argument('dst_addr', metavar='IP:PORT',
                    help='Fixed IP and port of the dst instance')
    ap.add_argument('dst_fip', help='Floating IP of the dst instance')

    ap.add_argument('-r', '--round', type=int, default=1,
                    help='Number of rounds for testing')
    ap.add_argument('--add_round', type=int, default=1,
                    help='Additional round for testing')

    if len(sys.argv) == 1:
        ap.print_help()
        sys.exit()

    args = ap.parse_args()

    MIN_SF_NUM = args.min_sf
    MAX_SF_NUM = args.max_sf
    DST_ADDR = args.dst_addr
    DST_FIP = args.dst_fip
    TEST_ROUND = args.round
    ADD_ROUND = args.add_round

    # Command to run and kill gap_timer.py
    RUN_GTIMER = ''
    RUN_GTIMER += 'nohup python3 /home/ubuntu/ctime_timer.py '
    RUN_GTIMER += '-s %s ' % (DST_ADDR)
    RUN_GTIMER += '-r %s ' % TEST_ROUND

    KILL_CTIMER = "pkill -f 'python3 /home/ubuntu/ctime_timer.py'"

    # Command to run python forwarder
    RUN_FWD = ''
    RUN_FWD += 'nohup python3 /home/ubuntu/forwarder.py '
    RUN_FWD += '%s ' % DST_ADDR
    RUN_FWD += '> /dev/null 2>&1 &'
    print('[DEBUG] Cmd to run forwarder: %s' % RUN_FWD)

    print('[DEBUG] Dst addr: %s, Dst floating IP:%s' % (DST_ADDR, DST_FIP))
    run_test(args.mode)
