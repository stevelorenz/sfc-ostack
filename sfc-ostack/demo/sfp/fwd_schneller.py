#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Pretend to be a schneller UDP packet forwarder

Email: xianglinks@gmail.com
"""

import binascii
import logging
import socket
import sys
import threading
import time

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
handler = logging.StreamHandler()
formatter = logging.Formatter(fmt_str)
handler.setFormatter(formatter)
logger.addHandler(handler)

if __name__ == "__main__":

    debug = True

    logger.setLevel(level['ERROR'])

    if debug:
        logger.setLevel(level['DEBUG'])

    # Name of ingress and egress interfaces
    in_iface = 'eth1'
    out_iface = 'eth2'

    dst_mac = 'fa:16:3e:58:25:fb'
    dst_mac_b = binascii.unhexlify(dst_mac.replace(':', ''))
    dst_mac_len = len(dst_mac_b)

    try:
        recv_sock = socket.socket(
            # MARK: Be carefull !!!
            socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3)
        )
        send_sock = socket.socket(
            socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3)
        )
    except socket.error as error:
        logger.error(error)
        sys.exit(1)

    logger.debug(
        'Bind forwards recv socket to ingress interface: %s' % in_iface)
    recv_sock.bind((in_iface, 0))
    logger.debug(
        'Bind forwards send socket to egress interface: %s' % out_iface)
    send_sock.bind((out_iface, 0))

    pack_arr = bytearray(4096)

    recv_num = 0
    while True:
        pack_len = recv_sock.recv_into(pack_arr, 4096)
        recv_num += 1
        logger.debug('Recv a ingress packet, num: %d', recv_num)

        if debug:
            old_dst_mac_b = binascii.hexlify(pack_arr[0:dst_mac_len])
            logger.debug('Original MAC address: %s', old_dst_mac_b.decode())

        # Replace the dstination MAC address
        pack_arr[0:dst_mac_len] = dst_mac_b

        if debug:
            new_dst_mac_b = binascii.hexlify(pack_arr[0:dst_mac_len])
            logger.debug('New MAC address: %s', new_dst_mac_b.decode())

        send_sock.send(pack_arr[0:pack_len])
