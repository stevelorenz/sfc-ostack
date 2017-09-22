#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
"""
About : UDP Latency Measurement Tool

Email : xianglinks@gmail.com
"""

import argparse
import multiprocessing
import pickle
import socket
import sys
import time
import logging

fmt_str = '%(asctime)s %(levelname)-8s %(message)s'
level = {
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
    'ERROR': logging.ERROR
}
logger = logging.getLogger(__name__)

SERVER_BUFFER_SIZE = 1024


################################################################################
#                                 Client Func                                  #
################################################################################

def get_packet_payload(packet_n):
    """Get packet payload

    :param packet_n (int): Packet serial number
    """
    send_time_stmp = time.time()
    payload = pickle.dumps((packet_n, send_time_stmp))
    return payload


def recv_packets(port, n_packets, payload_len, output_file):
    """
    Receive packets bounced back from the server. Calculate the round-trip
    latency for each packet by comparing the transmission timestamp
    contained within the packet to the system time at time of packet
    receipt.
    """

    sock_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                            socket.IPPROTO_UDP)
    sock_in.bind(('', port))
    logger.debug('Client bind port %d' % port)
    sock_in.settimeout(10)

    rev_packets = []
    try:
        while len(rev_packets) < n_packets:
            packet = sock_in.recv(payload_len)
            recv_time_stmp = time.time()
            # Strip fulling bytes
            payload = packet.rstrip(b'a')
            (packet_n, send_time_stmp) = pickle.loads(payload)
            latency_us = (recv_time_stmp - send_time_stmp) * 1e6
            rev_packets.append((packet_n, latency_us))
    except socket.timeout:
        print("Error: Timed out waiting to receive packets")
        print("So far had received %d packets" % len(rev_packets))

    print("Received %d/%d packets back from server" % (len(rev_packets),
                                                       n_packets))

    sock_in.close()
    # Save latency in a csv file
    with open(output_file, 'w') as out_file:
        out_file.write("%d\n" % n_packets)
        for tup in rev_packets:
            packet_n = tup[0]
            latency = "%.2f" % tup[1]
            out_file.write("%s,%s\n" % (packet_n, latency))


def send_packets(ip, port, n_packets, payload_len, send_rate):
    # Send rate in bytes/s
    # Number of packet per second
    packet_rate = send_rate / payload_len
    packet_interval = 1.0 / packet_rate
    logger.debug('Packet interval %.5f', packet_interval)

    sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_out.connect((ip, port))

    print("Sending %d %d-byte packets at about %d B/s to %s:%d..." %
          (n_packets, payload_len, send_rate, ip, port))

    send_start_stmp = time.time()

    for packet_n in range(n_packets):
        tx_start_stmp = time.time()
        payload = get_packet_payload(packet_n)
        n_fill_bytes = payload_len - len(payload)
        fill_char = b'a'
        payload = payload + n_fill_bytes * fill_char
        sock_out.sendall(payload)
        tx_end_stmp = time.time()

        tx_time_sec = tx_end_stmp - tx_start_stmp
        sleep_time_sec = packet_interval - tx_time_sec
        logger.debug('Send packet_n: %d, Sleep time %.3f' %
                     (packet_n, sleep_time_sec))
        if sleep_time_sec > 0:
            time.sleep(sleep_time_sec)

    send_end_stmp = time.time()
    print("Finished sending packets!")

    total_duration = send_end_stmp - send_start_stmp
    n_bytes = n_packets * payload_len
    bytes_per_sec = n_bytes / total_duration
    print("(Actually sent packets at %.5f kB/s)" % (bytes_per_sec / 1e3))
    sock_out.close()


def run_client(ip, port, n_packets, payload_len, send_rate, output_file):
    """Run client"""
    sender = multiprocessing.Process(
        target=send_packets,
        args=(ip, port, n_packets, payload_len, send_rate)
    )

    listen_port = port + 1
    receiver = multiprocessing.Process(
        target=recv_packets,
        args=(listen_port, n_packets, payload_len, output_file))

    receiver.start()
    sender.start()

    # Block main process until sub-process finished
    sender.join()
    receiver.join()


################################################################################
#                                 Server Func                                  #
################################################################################


def run_server(ip, port):
    sock_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                            socket.IPPROTO_UDP)
    sock_in.bind((ip, port))

    sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                             socket.IPPROTO_UDP)
    packet_n = 0
    while True:
        try:
            data, recv_addr = sock_in.recvfrom(SERVER_BUFFER_SIZE)
            logger.debug('Receive packet %d from client: %s:%d' %
                         (packet_n, ip, port))
            packet_n += 1
            if not data:
                print('Empty data received, exit...')
                break
            send_addr = (recv_addr[0], port + 1)
            sock_out.sendto(data, send_addr)
        except KeyboardInterrupt:
            print('Interrupt detected, exit...')
            break
    sock_in.close()
    sock_out.close()
    sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='UDP Latency Measurement Tool',
        formatter_class=argparse.RawTextHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-s', '--server', metavar='Address', type=str,
                       help='Run in UDP server mode')

    group.add_argument('-c', '--client', metavar='Address', type=str,
                       help='Run in UDP client mode')
    parser.add_argument("--n_packets", type=int, default=10,
                        help='Number of packets')
    parser.add_argument("--payload_len", type=int, default=512,
                        help='Length of packet in bytes')
    parser.add_argument("--send_rate", type=float, default=512,
                        help='Send rate in bytes/s')
    parser.add_argument("--mode", choices=['RTT'], default='RTT',
                        help='Measurement Mode. RTT: Round Trip Time')
    parser.add_argument("--log_level", choices=['INFO', 'DEBUG'], default='INFO',
                        help='Logging level')
    parser.add_argument("--output_file", default='latency.log', type=str,
                        help='Result output file path')
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level,
                        handlers=[logging.StreamHandler()],
                        format=fmt_str)

    if args.server:
        ip, port = args.server.split(':')
        port = int(port)
        print('------------------------------------------------------------')
        print('UDP server listening on %s, port %d' % (ip, port))
        if args.mode == 'RTT':
            print('- Received packets are sent back to port %d' % (port + 1))
        print('------------------------------------------------------------')
        run_server(ip, port)

    if args.client:
        if args.payload_len > SERVER_BUFFER_SIZE:
            logger.error('Payload length is larger than server buffer size!')
            sys.exit(1)
        ip, port = args.client.split(':')
        port = int(port)
        print('------------------------------------------------------------')
        print('UDP client connected to %s, port %d' % (ip, port))
        print('- Send packets to port %d' % port)
        print('- Receive packets from port %d' % (port + 1))
        print('------------------------------------------------------------')
        run_client(ip, port, args.n_packets, args.payload_len,
                   args.send_rate, args.output_file)
