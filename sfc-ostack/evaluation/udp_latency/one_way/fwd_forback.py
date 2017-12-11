#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Forwarding forwards and backwards SFC traffic

MARK : This is the one that really works...

Email: xianglinks@gmail.com
"""

import binascii
import logging
import multiprocessing
import socket
import struct
import sys

############
#  Config  #
############

# MAC address of source and destination instances in the SFC
SRC_MAC = 'fa:16:3e:04:07:36'  # MAC of the Proxy
DST_MAC = 'fa:16:3e:58:25:fb'

BUFFER_SIZE = 8192  # bytes

SRC_MAC_B = binascii.unhexlify(SRC_MAC.replace(':', ''))
DST_MAC_B = binascii.unhexlify(DST_MAC.replace(':', ''))
MAC_LEN = len(DST_MAC_B)

#############
#  Logging  #
#############

fmt_str = '%(asctime)s %(levelname)-8s %(processName)s %(message)s'
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
logger.setLevel(level['ERROR'])


#####################
#  Forward Program  #
#####################

def bind_raw_sock_pair(in_iface, out_iface):
    """Create and bind raw socket pairs"""
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

    recv_sock.bind((in_iface, 0))
    send_sock.bind((out_iface, 0))

    return (recv_sock, send_sock)


def forwards_forward(recv_sock, send_sock):
    """forwards_forward"""
    pack_arr = bytearray(BUFFER_SIZE)

    while True:
        pack_len = recv_sock.recv_into(pack_arr, BUFFER_SIZE)

        eth_typ = struct.unpack('>H', pack_arr[12:14])[0]
        # Only forward IPv4 packet
        if eth_typ == 2048:
            pack_arr[0:MAC_LEN] = DST_MAC_B
            send_sock.send(pack_arr[0:pack_len])


def backwards_forward(recv_sock, send_sock):
    """backwards_forward"""
    pack_arr = bytearray(BUFFER_SIZE)

    while True:
        pack_len = recv_sock.recv_into(pack_arr, BUFFER_SIZE)

        # Check if this is a forwards packet
        cur_dst_mac_b = pack_arr[0:MAC_LEN]
        if cur_dst_mac_b == DST_MAC_B:
            continue
        else:
            eth_typ = struct.unpack('>H', pack_arr[12:14])[0]
            # Only forward IPv4 packet
            if eth_typ == 2048:
                pack_arr[0:MAC_LEN] = SRC_MAC_B
                send_sock.send(pack_arr[0:pack_len])


if __name__ == "__main__":

    if len(sys.argv) < 2:
        PL_A_LEN = 1
        CTL_IP = '192.168.12.10'
        CTL_PORT = 6666

        ingress_iface = 'eth1'
        egress_iface = 'eth2'
    else:
        PL_A_LEN = sys.argv[1]
        CTL_IP = sys.argv[2]
        CTL_PORT = int(sys.argv[3])

        ingress_iface = sys.argv[4]
        egress_iface = sys.argv[5]

    # Bind sockets and start forwards and backwards processes
    recv_sock, send_sock = bind_raw_sock_pair(ingress_iface, egress_iface)
    fw_proc = multiprocessing.Process(target=forwards_forward,
                                      args=(recv_sock, send_sock))

    recv_sock, send_sock = bind_raw_sock_pair(egress_iface, ingress_iface)
    bw_proc = multiprocessing.Process(target=backwards_forward,
                                      args=(recv_sock, send_sock))
    fw_proc.start()
    bw_proc.start()

    # Send a ready packet to SFC manager
    ctl_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ctl_sock.sendto(b'ready', (CTL_IP, CTL_PORT))
    ctl_sock.close()

    fw_proc.join()
    bw_proc.join()
