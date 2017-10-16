#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
About : Timer for SFC start time
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

# Minus len for send time stamp
MAX_ALLOWED_UDP_PAYLOAD = (512 - 18)
RECV_BUFFER_SIZE = 512


def run_server_pm(addr, output_file=False):
    """Run UDP server with payload modification mode

    - The client send packet(payload) with first byte b'a' - old payload
    - The SFs in the chain modify the first byte to b'b' - new payload

    :return sfc_ts_lst (list): A list of time stamps for SFC
    """
    round_num = 0
    last_old_pload_ts = 0  # time stamp for last old payload
    # List of SFC creation latency
    sfc_ts_lst = list()
    chn_created = False

    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                              socket.IPPROTO_UDP)
    recv_sock.bind(addr)
    recv_sock.settimeout(None)

    try:
        while round_num < TEST_ROUND:
            # For current test round
            ct_ts_lst = list()
            pack = recv_sock.recv(RECV_BUFFER_SIZE)

            # SFC is not created
            if pack.startswith(b'a'):
                chn_created = False
                # Update time stamp for old payload
                last_old_pload_ts = time.time()  # float
                logger.debug('Recv a A packet. last ts: %s' %
                             last_old_pload_ts)

            if pack.startswith(b'b'):
                recv_bpack_ts = time.time()  # float
                logger.debug('Recv a B packet. ts: %s' % recv_bpack_ts)
                if not chn_created:
                    logger.debug('SFC is just created.')
                    chn_created = True
                    # Total SFC creation delay
                    # Unpack time stamp data in the payload
                    ts_str = pack.decode('ascii')
                    logger.debug('Time stamp str before strip: %s' % ts_str)
                    ts_str = ts_str.lstrip('b')
                    logger.debug('Time stamp str after strip: %s' % ts_str)
                    # A list of time stamps
                    # SF1_recv_ts, SF1_send_ts, SF2_recv_ts, SF2_send_ts
                    ct_ts_lst.append(last_old_pload_ts)
                    ts_lst = ts_str.split(',')
                    ts_lst.append(recv_bpack_ts)
                    ct_ts_lst.extend(map(float, ts_lst))
                    # cr_chn_ts_str = ','.join(map(str, ct_ts_lst))
                    # logger.debug('Current ct str %s' % cr_chn_ts_str)
                    sfc_ts_lst.append(ct_ts_lst)
                    round_num += 1
                else:
                    logger.debug('SFC is already created.')
                    logger.debug('Payload: %s' % pack.decode('ascii'))
    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt')
        sys.exit(0)
    else:
        logger.debug('Finish %d rounds of tests' % TEST_ROUND)

        if output_file:
            with open('./hello.csv', 'w+') as test_f:
                pass
            # Store test result in a csv file
            with open(OUTPUT_FILE, 'w') as out_file:
                for ts_lst in sfc_ts_lst:
                    ts_lst = filter(lambda x: x != '', ts_lst)
                    for ts in ts_lst:
                        out_file.write("%s," % ts)
                    out_file.write("\n")
    finally:
        recv_sock.close()
        return sfc_ts_lst


def run_client(addr):
    send_sock = socket.socket(socket.AF_INET,)
    """Run UDP Client

    MARK: The accuracy of the time.sleep() depends on the underlying OS
    The OS usually ONLY support millisecond sleeps
    """
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    base_payload = b'a' * PAYLOAD_LEN
    try:
        while True:
            # Send time stamp
            send_ts_b = str(time.time()).encode('ascii')
            payload = b','.join((base_payload, send_ts_b))
            logger.debug('Send payload: %s' % payload.decode('ascii'))
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
    parser.add_argument('-m', '--mode', type=str,
                        choices=['pm'], help='Mode for measurements')
    parser.add_argument('-d', '--max_delay', type=float, default=0.005,
                        help='Maximal allowed packet latency in second')
    parser.add_argument('-r', '--round', type=int, default=5,
                        help='Number of test rounds')
    parser.add_argument('-o', '--output_file', type=str, default='chn_ct.csv',
                        help='Output file of test result')

    group.add_argument('-c', '--client', metavar='Address', type=str,
                       help='Run in UDP client mode')
    parser.add_argument('--send_interval', type=float, default=0.001,
                        help='Client send interval in second')
    parser.add_argument('--payload_len', type=int, default=1,
                        help='Client payload length')

    parser.add_argument('-l', '--log_level', type=str, help='Logging level',
                        default='INFO')
    parser.add_argument('--log_handler', type=str, help='Logging handler',
                        choices=['console', 'file'], default='console')

    args = parser.parse_args()

    # MARK: Only used for testing...
    if args.log_handler == 'file':
        handler = logging.handlers.RotatingFileHandler(
            './ctime_timer.log', mode='a', maxBytes=5000000, backupCount=5)
    if args.log_handler == 'console':
        handler = logging.StreamHandler()

    logging.basicConfig(level=args.log_level,
                        handlers=[handler],
                        format=fmt_str)

    if args.server:
        ip, port = args.server.split(':')
        addr = (ip, int(port))
        TEST_ROUND = args.round
        OUTPUT_FILE = args.output_file
        if args.mode == 'pm':
            info_str = ('Run in payload modification mode.')
            logger.info('Run UDP server on %s:%s. %s' % (ip, port, info_str))
            run_server_pm(addr)

    if args.client:
        SEND_INTERVAL = args.send_interval
        PAYLOAD_LEN = args.payload_len
        if PAYLOAD_LEN > MAX_ALLOWED_UDP_PAYLOAD:
            logger.error('Maximal allowed UDP payload length is %d' %
                         MAX_ALLOWED_UDP_PAYLOAD)
            sys.exit(1)
        ip, port = args.client.split(':')
        addr = (ip, int(port))
        info_str = (
            'Send interval: %s seconds, payload length: %s bytes'
            % (SEND_INTERVAL, PAYLOAD_LEN)
        )
        logger.info('Run UDP Client on %s:%s.\n%s' % (ip, port, info_str))
        run_client(addr)
