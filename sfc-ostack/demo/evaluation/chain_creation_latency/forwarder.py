#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Forward packet and add a time stamp in the payload
       Use threading

Email: xianglinks@gmail.com
"""

import logging
import queue
import socket
import sys
import threading
import time


def send():
    """Send packets to dst instance"""
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                              socket.IPPROTO_UDP)
    send_sock.settimeout(None)
    while True:
        old_pack, recv_ts = pack_que.get()
        # Replace the first b'a'
        tmp_pack = old_pack.replace(b'a', b'b', 1)
        # time stamp in bytes, encode with ascii
        recv_ts_b = recv_ts.encode('ascii')
        send_ts_b = str(time.time()).encode('ascii')
        # Send new packet payload
        # b'b', recv_ts, send_ts,
        new_pack = b','.join(
            (tmp_pack, recv_ts_b, send_ts_b)
        )
        send_sock.sendto(new_pack, (DST_IP, DST_PORT))


def recv():
    """Recv packets from OVS local"""
    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                              socket.IPPROTO_UDP)
    recv_sock.bind((RECV_IP, RECV_PORT))
    recv_sock.settimeout(None)
    while True:
        pack = recv_sock.recv(BUFFER_SIZE)
        # Recv time stamp
        recv_ts = str(time.time())
        # Use blocking
        pack_que.put(
            (pack, recv_ts)
        )


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print('[Error] Missing IP and port of the dst instance.')
        print('[Usage] python3 ./forwarder.py IP:PORT')
        sys.exit(1)

    # Addr for dst instance
    ip, port = sys.argv[1].split(':')
    DST_IP = ip
    DST_PORT = int(port)

    # IP of OVS local port
    RECV_IP = "192.168.0.1"
    RECV_PORT = 9999

    BUFFER_SIZE = 1024
    # FIFO queue of packets
    pack_que = queue.Queue()

    # Run recv and send thread
    recv_thread = threading.Thread(target=recv).start()
    send_thread = threading.Thread(target=send).start()

    # Block main thread
    recv_thread.join()
    send_thread.join()
