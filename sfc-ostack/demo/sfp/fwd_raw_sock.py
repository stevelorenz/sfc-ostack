#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: UDP packet forwarder using raw socket

Email: xianglinks@gmail.com
"""

import socket
import struct
import sys
import time


##############
#  Forwards  #
##############

def fw_recv_pack(in_iface):
    """Recv packet from ingress interface

    :param in_iface (str): Name of ingress interface
    """
    try:
        recv_sock = socket.socket(
            socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3)
        )
    except socket.error as error:
        print(error)
        sys.exit()

    print('Bind raw socket to interface: %s' % in_iface)
    recv_sock.bind((in_iface, 0))

    while True:
        data = recv_sock.recv(1024)
        recv_sock.send(data)


###############
#  Backwards  #
###############


if __name__ == "__main__":

    in_iface = 'eth1'
    out_iface = 'eth2'
