#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About : A UDP receiver

Email : xianglinks@gmail.com
"""

import socket
import sys

UDP_IP = "10.0.0.Y"
UDP_PORT = 9999

sock = socket.socket(socket.AF_INET,
                     socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

try:
    while True:
        data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
        print("Received message: %s " % data)
except KeyboardInterrupt:
    sys.exit()
