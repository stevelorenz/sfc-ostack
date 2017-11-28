#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: UDP packet forwarder using raw socket

Email: xianglinks@gmail.com
"""

import logging
import socket
import ipdb
import struct
import time
import sys


if __name__ == "__main__":

    DST_IP = '127.0.0.1'

    try:
        recv_sock = socket.socket(
            socket.AF_PACKET, socket.SOCK_RAW, socket.htons(1))
    except socket.error as error:
        print(error)
        sys.exit()

    while True:
        ipdb.set_trace()
        data = recv_sock.recv(1024)
        print(data.decode('ascii'))
        time.sleep(1)
