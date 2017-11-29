#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: UDP packet forwarder using raw socket

Email: xianglinks@gmail.com
"""

import argparse
import logging
import socket
# import struct
import sys
import threading
import time

"""
MARK:
    - Recv all packet
    - Only handle UDP packet
    - Parse packet to get IP header and UDP payload
    - Modify the payload
    - Recalculate the checksum
    - Send packet out
"""

#############
#  Logging  #
#############

fmt_str = '%(asctime)s %(levelname)-8s %(message)s'
level = {
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
    'ERROR': logging.ERROR
}

logger = logging.getLogger(__name__)
logger.setLevel(level['DEBUG'])
handler = logging.StreamHandler()
formatter = logging.Formatter(fmt_str)
handler.setFormatter(formatter)
logger.addHandler(handler)


##############
#  Forwards  #
##############

def fw_recv_pack(in_iface):
    """Recv packet from ingress interface

    :param in_iface (str): Name of ingress interface
    """
    try:
        recv_sock = socket.socket(
            # MARK: Be carefull !!!
            socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3)
        )
    except socket.error as error:
        logger.error(error)
        sys.exit(1)

    logger.info('Bind raw socket to ingress interface: %s' % in_iface)
    recv_sock.bind((in_iface, 0))

    recv_num = 0
    while True:
        data = recv_sock.recv(4096)
        recv_num += 1
        logger.debug(
            'Receive a packet from ingress interface, len: %d' % len(data))
        recv_sock.send(data)


###############
#  Backwards  #
###############

def bw_recv_pack(out_iface):
    """Recv packet from egress interface"""
    try:
        recv_sock = socket.socket(
            socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3)
        )
    except socket.error as error:
        logger.error(error)
        sys.exit(1)

    logger.info('Bind raw socket to egress interface: %s' % out_iface)
    recv_sock.bind((out_iface, 0))

    recv_num = 0
    while True:
        data = recv_sock.recv(4096)
        recv_num += 1
        logger.debug(
            'Receive a packet from egress interface, len: %d' % len(data))
        recv_sock.send(data)


if __name__ == "__main__":

    in_iface = 'eth1'
    out_iface = 'eth2'

    fw_thread = threading.Thread(target=fw_recv_pack, args=(in_iface, ))
    bw_thread = threading.Thread(target=bw_recv_pack, args=(out_iface, ))

    fw_thread.start()
    bw_thread.start()

    fw_thread.join()
    bw_thread.join()
