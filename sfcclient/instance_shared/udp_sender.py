#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About : A UDP sender

Email : xianglinks@gmail.com
"""

import socket
import sys

UDP_IP = "10.0.0.Y"
UDP_PORT = 9999
MESSAGE = "Hello, World!"

print("UDP target IP: %s" % UDP_IP)
print("UDP target port: %s" % UDP_PORT)
print("message: %s" % MESSAGE)

cl_sock = socket.socket(socket.AF_INET,
                        socket.SOCK_DGRAM)

# MARK: set source IP and port
cl_sock.bind(('10.0.0.X', 8888))

try:
    while True:
        cl_sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
except KeyboardInterrupt:
    sys.exit()
