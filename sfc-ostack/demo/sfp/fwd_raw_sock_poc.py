#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: UDP packet forwarder using raw socket

Email: xianglinks@gmail.com
"""

import binascii
import logging
import socket
import sys
import threading
import time

import dpkt

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


def print_eth_bin(pack):
    """Print binary pack as a ethernet frame"""
    eth = dpkt.ethernet.Ethernet(pack)
    src_mac = binascii.hexlify(eth.src).decode()
    dst_mac = binascii.hexlify(eth.dst).decode()
    ip = eth.data
    src_ip = socket.inet_ntoa(ip.src)
    dst_ip = socket.inet_ntoa(ip.dst)
    logger.info('src_mac: %s, dst_mac:%s; src_ip: %s, dst_ip: %s',
                src_mac, dst_mac, src_ip, dst_ip)


##############
#  Forwards  #
##############

def fw_recv_pack(in_iface, out_iface):
    """Recv packet from ingress interface

    :param in_iface (str): Name of ingress interface
    """
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

    logger.info('Bind forwards recv socket to ingress interface: %s' % in_iface)
    recv_sock.bind((in_iface, 0))
    logger.info('Bind forwards send socket to egress interface: %s' % out_iface)
    send_sock.bind((out_iface, 0))

    recv_num = 0
    while True:
        pack = recv_sock.recv(4096)
        recv_num += 1
        logger.debug(
            'Receive a packet from ingress interface, len: %d' % len(pack))
        # print('--- Before Mod ---')
        # print_eth_bin(pack)
        pack = mod_fw_pack(pack)
        # print('--- After Mod ---')
        # print_eth_bin(pack)
        send_sock.send(pack)


def mod_fw_pack(pack):
    """Modify fowards packet"""
    dst_mac = 'fa:16:3e:58:25:fb'
    eth = dpkt.ethernet.Ethernet(pack)
    # src_mac_b = binascii.unhexlify(src_mac.replace(':', ''))
    dst_mac_b = binascii.unhexlify(dst_mac.replace(':', ''))
    # eth.src = src_mac_b
    eth.dst = dst_mac_b
    return bytes(eth)


###############
#  Backwards  #
###############

def bw_recv_pack(out_iface, in_iface):
    """Recv packet from egress interface"""
    try:
        recv_sock = socket.socket(
            socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3)
        )
        send_sock = socket.socket(
            socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3)
        )
    except socket.error as error:
        logger.error(error)
        sys.exit(1)

    logger.info('Bind backwards recv socket to egress interface: %s' % out_iface)
    recv_sock.bind((out_iface, 0))
    logger.info('Bind backwards send socket to ingress interface: %s' % in_iface)
    send_sock.bind((in_iface, 0))

    recv_num = 0
    while True:
        pack = recv_sock.recv(4096)
        recv_num += 1
        logger.debug(
            'Receive a packet from egress interface, len: %d' % len(pack))
        send_sock.send(pack)


if __name__ == "__main__":

    # Name of ingress and egress interfaces
    in_iface = 'eth1'
    out_iface = 'eth2'

    fw_thread = threading.Thread(
        target=fw_recv_pack, args=(in_iface, out_iface))
    bw_thread = threading.Thread(
        target=bw_recv_pack, args=(out_iface, in_iface))

    fw_thread.start()
    # bw_thread.start()

    fw_thread.join()
    # bw_thread.join()
