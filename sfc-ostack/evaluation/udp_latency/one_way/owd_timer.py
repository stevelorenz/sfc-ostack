#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: UDP one way delay timer

Email: xianglinks@gmail.com
"""

import argparse
import logging
import os
import signal
import socket
import sys
import time


def run_client():
    """Run UDP client"""

    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    send_idx = 0

    while send_idx < N_PACKETS:
        send_ts_str = str(time.time())
        pl_str = ','.join((str(send_idx), send_ts_str))
        pl_str = ','.join((pl_str, 'a' * (PAYLOAD_LEN - len(pl_str))))
        logger.debug('Send pack: %s', pl_str)
        send_sock.sendto(pl_str.encode('ascii'), SRV_ADDR)
        send_idx += 1
        time.sleep(SEND_INTERVAL)


def run_server():
    """Run UDP server"""

    cur_n_packets = N_PACKETS
    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                              socket.IPPROTO_UDP)

    recv_sock.bind(SRV_ADDR)
    recv_sock.settimeout(None)

    csv_file = open(OUTPUT_FILE, 'a+')

    def exit_server(*args):
        logger.debug('SIGTERM detected, save all data in the buffer and exit.')
        recv_sock.close()
        # Sync buffered data to the disk
        csv_file.flush()
        os.fsync(csv_file.fileno())
        csv_file.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, exit_server)

    try:
        for rd in range(1, ROUND + 1):
            recv_idx = 0
            logger.info('Current test round: %d' % rd)
            owd_result = list()
            while recv_idx < cur_n_packets:
                pack = recv_sock.recv(SRV_BUFFER_SIZE)
                recv_ts = time.time()
                send_idx, send_ts = pack.decode('ascii').split(',')[:2]
                send_idx = int(send_idx)
                if send_idx != recv_idx:
                    recv_idx = send_idx + 1
                    cur_n_packets = cur_n_packets - (send_idx + 1)
                    logger.debug(
                        'Packet order is not right! send_idx: %d, recv_idx: %d, cur_n_packet: %d',
                        send_idx, recv_idx, cur_n_packets
                    )
                    # Start calc owd from the next packet
                    continue
                send_ts = float(send_ts)
                logger.debug('Recv a pack, idx:%s, send_ts:%s',
                             send_idx, send_ts)
                owd = recv_ts - send_ts  # in second
                owd_result.append(owd)
                recv_idx += 1
            csv_file.write(
                ','.join(map(str, owd_result))
            )
            csv_file.write('\n')

    except Exception as e:
        csv_file.write(str(e))
        csv_file.write('\n')
    finally:
        recv_sock.close()
        csv_file.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Timer for UDP one way delay.',
        formatter_class=argparse.RawTextHelpFormatter
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-s', '--server', metavar='Address', type=str,
                       help='Run in UDP server mode')
    parser.add_argument('-o', '--output_file', type=str, default='udp_owd.csv',
                        help='Output file of test result')
    parser.add_argument('--srv_buffer', type=int, default=512,
                        metavar='Buffer Size',
                        help='Server recv buffer size in bytes')
    parser.add_argument('-r', '--round', type=int, default=1,
                        help='Number of sending rounds')

    group.add_argument('-c', '--client', metavar='Address', type=str,
                       help='Run in UDP client mode')
    parser.add_argument('--payload_len', type=int, default=512,
                        help='Client payload length in bytes')
    parser.add_argument("--send_interval", type=float, default=1.0,
                        help='Send interval in second')

    parser.add_argument('-n', '--n_packets', type=int,
                        help='Number of sent packets', default=10)
    parser.add_argument('-l', '--log_level', type=str, help='Logging level',
                        default='INFO')

    args = parser.parse_args()

    fmt_str = '%(asctime)s %(levelname)-8s %(message)s'
    level = {
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
        'ERROR': logging.ERROR
    }
    logger = logging.getLogger(__name__)

    logging.basicConfig(level=args.log_level,
                        handlers=[logging.StreamHandler()],
                        format=fmt_str)

    N_PACKETS = args.n_packets
    SRV_BUFFER_SIZE = args.srv_buffer
    ROUND = args.round

    if args.server:
        ip, port = args.server.split(':')
        SRV_ADDR = (ip, int(port))
        OUTPUT_FILE = args.output_file
        logger.info('Run UDP server listening on %s:%s.', ip, port)
        run_server()

    if args.client:
        ip, port = args.client.split(':')
        SRV_ADDR = (ip, int(port))
        SEND_INTERVAL = args.send_interval
        PAYLOAD_LEN = args.payload_len
        logger.info('Run UDP client sending to %s:%s.', ip, port)
        run_client()
