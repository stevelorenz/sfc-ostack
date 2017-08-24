#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About : A UDP sender

Email : xianglinks@gmail.com
"""

import socket
import sys
from time import gmtime, sleep, strftime

DST_UDP_IP = '10.0.0.Y'
DST_UDP_PORT = 9999
MESSAGE = 'Hello, World!'

# SRC_UDP_IP = '10.0.0.X'
# SRC_UDP_PORT = 8888

print('UDP target IP: %s' % DST_UDP_IP)
print('UDP target port: %s' % DST_UDP_PORT)
print('Message: %s' % MESSAGE)

cl_sock = socket.socket(socket.AF_INET,
                        socket.SOCK_DGRAM)

# MARK: set source IP and port
# cl_sock.bind((SRC_UDP_IP, SRC_UDP_PORT))

try:
    while True:
        CUR_MSG = ' '.join(
            [strftime("%Y-%m-%d %H:%M:%S", gmtime()), MESSAGE]
        )
        cl_sock.sendto(CUR_MSG, (DST_UDP_IP, DST_UDP_PORT))
        sleep(0.5)
except KeyboardInterrupt:
    sys.exit()
