#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Run SFC creation time measurements

Email: xianglinks@gmail.com
"""

import argparse
import paramiko
import sys


def lk_forwarding_test():
    print('[TEST] Test chain creation time with kernel forwarding')
    pass


def py_forwarding_test():
    pass


if __name__ == "__main__":

    ap = argparse.ArgumentParser(description='Run UDP RTT latency test.')
    ap.add_argument('fw', help='Forwarding method',
                    choices=['kernel', 'python'])
    ap.add_argument('min_sf', type=int, help='Minimal number of SF server')
    ap.add_argument('max_sf', type=int, help='Maximal number of SF server')
    ap.add_argument('test_round', type=int, help='Number of test rounds')

    ap.add_argument('--dst_ip', type=str,
                    help='Fixed IP of the dst instance')
    ap.add_argument('--port', type=int, default=9999,
                    help='Listening port of the dst instance')
    ap.add_argument('--dst_fip', type=str,
                    help='Floating IP of the dst instance')

    if len(sys.argv) == 1:
        ap.print_help()
        sys.exit()
    args = ap.parse_args()

    # MARK: Used for SSH
    DST_FIP = args.dst_fip
    MAX_ALLOWED_DELAY = 0.01  # 10ms
    # Command to run and kill ctime_timer.py on server instance
    RUN_CTIMER = ''
    RUN_CTIMER += 'nohup python3 /home/ubuntu/ctime_timer.py '
    RUN_CTIMER += '-s %s:%s ' % (args.dst_ip, args.port)
    RUN_CTIMER += '-d %s ' % MAX_ALLOWED_DELAY
    RUN_CTIMER += '-r %s' % args.test_round
    KILL_CTIMER = "pkill -f 'nohup python3 /home/ubuntu/ctime_timer.py'"

    if args.fw == 'python':
        INIT_SCRIPT = './init_py_forwarding.sh'
        py_forwarding_test()
    elif args.fw == 'kernel':
        INIT_SCRIPT = './init_lk_forwarding.sh'
        lk_forwarding_test()
