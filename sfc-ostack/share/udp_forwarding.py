#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About : UDP forwarding

Email : xianglinks@gmail.com
"""

import socket

if __name__ == "__main__":

    SEND_UDP_IP = '10.0.0.7'
    SEND_UDP_PORT = 9999

    # The BRIDGE_IP in ./init_sf.sh
    RECV_UDP_IP = "192.168.0.1"
    RECV_UDP_PORT = 9999

    sock = socket.socket(socket.AF_INET,
                         socket.SOCK_DGRAM)
    sock.bind((RECV_UDP_IP, RECV_UDP_PORT))

    print('Start UDP forwarding...')
    recv_num = 0
    while True:
        data, addr = sock.recvfrom(1024)
        sock.sendto(data, (SEND_UDP_IP, SEND_UDP_PORT))
