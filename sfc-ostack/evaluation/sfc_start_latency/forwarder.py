#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Forward packet and add a time stamp in the payload
       Use threading

Email: xianglinks@gmail.com
"""

import argparse
import logging
import queue
import socket
import sys
import threading
import time

# Logger settings
fmt_str = '%(threadName)s %(asctime)s %(levelname)-8s %(message)s'
level = {
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
    'ERROR': logging.ERROR
}
logger = logging.getLogger(__name__)


def send():
    """Send packets to dst instance"""
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                              socket.IPPROTO_UDP)
    send_sock.settimeout(None)
    while True:
        old_pack, recv_ts = pack_que.get()
        # Replace the first b'a'
        tmp_pack = old_pack.replace(b'a', b'b', 1)
        # time stamp in bytes, encode with ascii
        recv_ts_b = recv_ts.encode('ascii')
        send_ts_b = str(time.time()).encode('ascii')
        # Send new packet payload
        # b'b', recv_ts, send_ts,
        new_pack = b','.join(
            (tmp_pack, recv_ts_b, send_ts_b)
        )
        logger.debug('Send new pack:%s' % new_pack.decode('ascii'))
        send_sock.sendto(new_pack, (DST_IP, DST_PORT))


def recv():
    """Recv packets from OVS local"""
    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                              socket.IPPROTO_UDP)
    recv_sock.bind((RECV_IP, RECV_PORT))
    recv_sock.settimeout(None)
    while True:
        pack = recv_sock.recv(BUFFER_SIZE)
        # Recv time stamp
        recv_ts = str(time.time())
        logger.debug('Recv pack: %s, ts: %s'
                     % (pack.decode('ascii'), recv_ts))
        # Use blocking
        pack_que.put(
            (pack, recv_ts)
        )


def resp_mgn():
    """TODO: Open a socket for responsing the manage messages from central
    controller"""
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Python UDP forwarder',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('dst_addr', type=str,
                        help='Addr of destination instance.')
    parser.add_argument('-l', '--log_level', type=str, help='Logging level',
                        default='INFO')

    args = parser.parse_args()
    logging.basicConfig(level=args.log_level,
                        handlers=[logging.StreamHandler()],
                        format=fmt_str)

    # Addr for dst instance
    ip, port = args.dst_addr.split(':')
    DST_IP = ip
    DST_PORT = int(port)

    # IP of OVS local port
    RECV_IP = "192.168.0.1"
    RECV_PORT = 9999

    BUFFER_SIZE = 1024
    # FIFO queue of packets
    pack_que = queue.Queue()

    # Run recv and send thread
    recv_thread = threading.Thread(target=recv)
    send_thread = threading.Thread(target=send)
    recv_thread.start()
    send_thread.start()

    # Block main thread
    recv_thread.join()
    send_thread.join()
