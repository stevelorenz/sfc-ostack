#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Run SFC creation time measurements
       * Based on payload modification(pm)

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


def _get_floating_ip(pt_name):
    ins_port = conn.network.find_port(pt_name)
    fip = list(conn.network.ips(port_id=ins_port.id))[0].floating_ip_address
    return fip


def test_ct_pyf():
    """Test chain creation time with python forwarding

    MARK: SHOULD be split into small funcs...
    """
    print('[TEST] Test SFC creation time with python forwarding.')

    for srv_num in range(MIN_SF_NUM, MAX_SF_NUM + 1):
        if not DEBUG_MODE:
            outfile_name = 'cen-pyf-%d-cctime-pm.csv' % srv_num
            CRT_RUN_CTIMER = RUN_CTIMER
            CRT_RUN_CTIMER += '-o %s ' % outfile_name
            CRT_RUN_CTIMER += '> /dev/null 2>&1 &'
            print('[DEBUG] Cmd for running CTimer: %s' % CRT_RUN_CTIMER)
            # Run timer on the dst instance
            ssh_clt = paramiko.SSHClient()
            ssh_clt.set_missing_host_key_policy(paramiko.AutoAddPolicy())
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

        print('[DEBUG] Start creating and deleting SFC')
        for round_num in range(1, TEST_ROUND + 1):
            time.sleep(15)  # recv some A packets
            print('[DEBUG] Create %d SFs' % srv_num)
            subprocess.run(
                ['python3', '../sfc_mgr.py', SFC_CONF,
                    INIT_SCRIPT, 'create', '%d' % srv_num],
                check=True)

            time.sleep(20)  # recv some B packets

            if not DEBUG_MODE:
                print('[DEBUG] Delete %d SFs' % srv_num)
                subprocess.run(
                    ['python3', '../sfc_mgr.py', SFC_CONF,
                        INIT_SCRIPT, 'delete', '%d' % srv_num],
                    check=True)
                time.sleep(3)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description='Run SFC creation time test.')
    ap.add_argument('min_sf', type=int, help='Minimal number of SF server')
    ap.add_argument('max_sf', type=int, help='Maximal number of SF server')
    ap.add_argument('-r', '--round', type=int, default=1,
                    help='Number of rounds for testing')
    ap.add_argument('dst_addr', metavar='IP:PORT',
                    help='Fixed IP and port of the dst instance')
    ap.add_argument('dst_fip', help='Floating IP of the dst instance')

    ap.add_argument('--clean', help='Clear created SFC resouces, used for tests',
                    action='store_true')
    ap.add_argument('--full_clean',
                    help='Also kill ctime_timer process on dst instance',
                    action='store_true')
    ap.add_argument('--debug', help='Run in debug mode...',
                    action='store_true')

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

    if args.clean or args.full_clean:
        print('[INFO] Run simple clean func')
        for srv_num in range(MIN_SF_NUM, MAX_SF_NUM + 1):
            try:
                subprocess.run(
                    ['python3', '../sfc_mgr.py', SFC_CONF,
                        INIT_SCRIPT, 'delete', '%d' % srv_num],
                    check=True)
            except Exception:
                pass
            if args.full_clean:
                ssh_clt = paramiko.SSHClient()
                ssh_clt.set_missing_host_key_policy(paramiko.AutoAddPolicy())
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
                    print('[DEBUG] Kill ctime_timer on recv instance.')
                    channel.exec_command(KILL_CTIMER)
                    status = channel.recv_exit_status()
                    print('[DEBUG] ctime_timer process status: %d' % status)
                ssh_clt.close()
            sys.exit(0)

    DEBUG_MODE = args.debug

    print('[DEBUG] Dst addr: %s, Dst floating IP:%s' % (DST_ADDR, DST_FIP))

    test_ct_pyf()
