#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
About : Timer for SFC creation time
        Try to have high accuracy

Email : xianglinks@gmail.com
"""

import argparse
import logging
import logging.handlers
import socket
import sys
import time
from collections import deque

# Logger settings
fmt_str = '%(asctime)s %(levelname)-8s %(message)s'
level = {
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
    'ERROR': logging.ERROR
}
logger = logging.getLogger(__name__)


def run_server(addr):
    """Run UDP server"""
    round_num, pack_num = 0, 0
    # Store chain creation time
    chn_ct_lst = list()
    # Queue to store time stamps of received packets
    recv_ts_que = deque(maxlen=int(1e6))
    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                              socket.IPPROTO_UDP)
    recv_sock.bind(addr)
    recv_sock.settimeout(600)
    logger.debug('Recv socket is ready, bind to %s:%s' % (addr))
    try:
        while round_num < TEST_ROUND:
            pack = recv_sock.recv(BUFFER_SIZE)
            now_ts = time.time()
            pack_num += 1
            if len(recv_ts_que) == 0:
                logger.debug('Recv first packet, recv_ts: %f' % (now_ts))
                recv_ts_que.append(now_ts)
            # Check the recv delay
            else:
                last_ts = recv_ts_que[-1]
                logger.debug('Time stamp: now: %f, last: %f' %
                             (now_ts, last_ts))
                delay = now_ts - last_ts
                recv_ts_que.append(now_ts)
                logger.debug('Recv packet number: %d, delay:%.3f' %
                             (pack_num, delay))
                # SHOULD be chain creation delay
                if delay >= MAX_ALLOWED_DELAY:
                    chn_ct_lst.append(delay)
                    round_num += 1
                    logger.debug('[CT_Delay] delay: %f, round_num: %d'
                                 % (delay, round_num))
    except socket.timeout:
        logger.error('Recv socket timeout!')
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt')
        sys.exit(0)
    else:
        # Store test result in a csv file
        with open(OUTPUT_FILE, 'w') as out_file:
            for delay in chn_ct_lst:
                out_file.write("%s\n" % delay)
    finally:
        recv_sock.close()


def run_client(addr):
    send_sock = socket.socket(socket.AF_INET,)
    """Run UDP Client

    MARK: The accuracy of the time.sleep() depends on the underlying OS
    The OS usually only support millisecond sleeps
    """
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = b'a' * PAYLOAD_LEN
    try:
        while True:
            send_sock.sendto(payload, addr)
            time.sleep(SEND_INTERVAL)
    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt')
        sys.exit(0)
    finally:
        send_sock.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Timer for SFC creation time.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-s', '--server', metavar='Address', type=str,
                       help='Run in UDP server mode')
    parser.add_argument('-d', '--max_delay', type=float,
                        help='Maximal allowed packet latency in second')
    parser.add_argument('-r', '--round', type=int, default=5,
                        help='Number of test rounds')
    parser.add_argument('-o', '--output_file', type=str, default='chn_ct.csv',
                        help='Output file of test result')

    group.add_argument('-c', '--client', metavar='Address', type=str,
                       help='Run in UDP client mode')
    parser.add_argument('--send_interval', type=float, default=0.001,
                        help='Client send interval in second')
    parser.add_argument('--payload_len', type=int, default=512,
                        help='Client payload length')

    parser.add_argument('-l', '--log_level', type=str, help='Logging level',
                        default='INFO')
    parser.add_argument('--log_handler', type=str, help='Logging handler',
                        choices=['console', 'file'], default='console')

    args = parser.parse_args()

    if args.log_handler == 'file':
        handler = logging.handlers.RotatingFileHandler(
            './ctime_timer.log', mode='a', maxBytes=5000000, backupCount=5)
    if args.log_handler == 'console':
        handler = logging.StreamHandler()

    logging.basicConfig(level=args.log_level,
                        handlers=[handler],
                        format=fmt_str)

    # Client
    SEND_INTERVAL = args.send_interval
    PAYLOAD_LEN = args.payload_len

    # Server
    # MARK: This parameter is import, theoretic difference SHOULD be 2 packets
    #       The minimal ratio SHOULD be 2 here
    if not args.max_delay:
        ALLOW_RATIO = 5.0
        MAX_ALLOWED_DELAY = ALLOW_RATIO * SEND_INTERVAL
    else:
        MAX_ALLOWED_DELAY = args.max_delay
    BUFFER_SIZE = PAYLOAD_LEN
    TEST_ROUND = args.round
    OUTPUT_FILE = args.output_file

    if args.server:
        ip, port = args.server.split(':')
        addr = (ip, int(port))
        info_str = 'Test round: %s, Max delay: %s' % (TEST_ROUND,
                                                      MAX_ALLOWED_DELAY)
        logger.info('Run UDP server on %s:%s.\n%s' % (ip, port, info_str))
        run_server(addr)

    if args.client:
        ip, port = args.client.split(':')
        addr = (ip, int(port))
        info_str = (
            'Send interval: %s seconds, payload length: %s bytes'
            % (SEND_INTERVAL, PAYLOAD_LEN)
        )
        logger.info('Run UDP Client on %s:%s.\n%s' % (ip, port, info_str))
        run_client(addr)
