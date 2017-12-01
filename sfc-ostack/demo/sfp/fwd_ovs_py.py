#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: UDP forwarding from OVS local port
Email: xianglinks@gmail.com
"""

import socket

if __name__ == "__main__":

    BUFFER_SIZE = 8192

    BR_IP = '192.168.0.1'
    BR_PORT = 9999

    DST_IP = '10.0.12.12'
    DST_PORT = 9999

    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                              socket.IPPROTO_UDP)

    recv_sock.bind((BR_IP, BR_PORT))

    while True:
        pack = recv_sock.recv(BUFFER_SIZE)
        recv_sock.sendto(pack, (DST_IP, DST_PORT))
