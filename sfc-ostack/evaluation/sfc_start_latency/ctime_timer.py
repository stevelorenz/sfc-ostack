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
import signal
import os
import socket
import sys
import time

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


def run_server_pm(addr):
    """Run UDP server with payload modification mode

    - The client send packet(payload) with first byte b'a' - old payload
    - The SFs in the chain modify the first byte to b'b' - new payload

    :return sfc_ts_lst (list): A list of time stamps for SFC
    """
    last_old_pload_ts = '0'  # time stamp for last old payload
    chn_created = False

    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                              socket.IPPROTO_UDP)
    recv_sock.bind(addr)
    recv_sock.settimeout(None)

    csv_file = open(OUTPUT_FILE, 'a+')

    def exit_server(*args):
        logger.debug('SIGTERM detected.')
        recv_sock.close()
        # Sync buffered data to the disk
        csv_file.flush()
        os.fsync(csv_file.fileno())
        csv_file.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, exit_server)

    try:
        # MARK: Keep running until the process is killed
        round_num = 0
        while True:
            pack = recv_sock.recv(RECV_BUFFER_SIZE)

            # if round_num % 2 == 0:
            #     pack = b'a1234'
            # else:
            #     pack = b'b,1234,5678'

            # time.sleep(1)

            # SFC is not created
            if pack.startswith(b'a'):
                chn_created = False
                # Update time stamp for old payload
                last_old_pload_ts = str(time.time())
                # Used for checking time sync status
                apack_info = (
                    'ts: %s, Recv a A packet: %s. last a pack ts: %s'
                    % (time.time(), pack.decode('ascii'), last_old_pload_ts)
                )
                logger.debug(apack_info)

            if pack.startswith(b'b'):
                recv_bpack_ts = str(time.time())
                logger.debug('Recv a B packet. ts: %s' % recv_bpack_ts)
                if not chn_created:
                    logger.debug('SFC is just created.')
                    chn_created = True
                    # Total SFC creation delay
                    # Unpack time stamp data in the payload
                    ts_str = pack.decode('ascii')
                    logger.debug('Time stamp str before strip: %s' % ts_str)
                    # SF1_recv_ts, SF1_send_ts, SF2_recv_ts, SF2_send_ts
                    # First element: bbb...
                    ts_lst = ts_str.split(',')[1:]
                    ts_lst.append(recv_bpack_ts)
                    ts_lst.append(last_old_pload_ts)
                    try:
                        csv_file.write(','.join(ts_lst))
                        csv_file.write('\n')
                    except ValueError:
                        sys.exit(0)
                else:
                    logger.debug('SFC is already created.')
                    logger.debug('Payload: %s' % pack.decode('ascii'))
            round_num += 1
    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt')
        sys.exit(0)


def run_client(addr):
    send_sock = socket.socket(socket.AF_INET,)
    """Run UDP Client

    MARK: The accuracy of the time.sleep() depends on the underlying OS
    The OS usually ONLY support millisecond sleeps
    """

    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def exit_client(*args):
        logger.debug('SIGTERM detected.')
        send_sock.close()
        sys.exit()

    signal.signal(signal.SIGTERM, exit_client)

    base_payload = b'a' * PAYLOAD_LEN
    while True:
        # Send time stamp
        send_ts_b = str(time.time()).encode('ascii')
        payload = b','.join((base_payload, send_ts_b))
        logger.debug('Send payload: %s' % payload.decode('ascii'))
        send_sock.sendto(payload, addr)
        time.sleep(SEND_INTERVAL)


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
