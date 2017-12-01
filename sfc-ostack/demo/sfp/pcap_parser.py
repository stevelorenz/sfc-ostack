#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About : Parse PCAP file of kernerl forwarded packet
Email : xianglinks@gmail.com
"""

import binascii
import socket
import struct
import sys

import dpkt


def test_dpkt():
    print('\n# Test dpkt')
    pack_num = 1
    # Load and parser pcap file
    with open('./lk_out.pcap', 'rb') as pcap_f:
        parsed_num = 0
        pcap = dpkt.pcap.Reader(pcap_f)
        for ts, buf in pcap:
            print('# TS: %f, len: %d' % (ts, len(buf)))
            eth = dpkt.ethernet.Ethernet(buf)

            print('## Ethernet Frame:')
            print('src_mac: %s' % (binascii.hexlify(eth.src).decode()))
            print('dst_mac: %s' % (binascii.hexlify(eth.dst).decode()))

            print('## IP Packet:')
            ip = eth.data
            print('packet len: %d' % ip.len)
            print('header len: %d' % ip.hl)
            print('src_ip: %s, dst_ip: %s' %
                  (socket.inet_ntoa(ip.src),
                   socket.inet_ntoa(ip.dst)))
            print('checksum: %x' % ip.sum)

            print('## UDP Segment:')
            udp = ip.data
            print('src_port: %d' % udp.sport)
            print('dst_port: %d' % udp.dport)
            print('checksum: %x' % udp.sum)
            # print('payload: %s' % binascii.hexlify(udp.data).decode())

            parsed_num += 1
            if parsed_num == pack_num:
                break


def test_bytearray():
    print('\n# Test bytearry')
    pack_num = 1

    ETH_LEN = 14
    IHL = 20

    with open('./lk_out.pcap', 'rb') as pcap_f:
        parsed_num = 0
        pcap = dpkt.pcap.Reader(pcap_f)
        for ts, buf in pcap:
            print('# TS: %f, len: %d' % (ts, len(buf)))
            pack = bytearray(buf)
            print('### Ethernet Frame:')
            print('length: %d' % len(pack))
            print('Type: %d' % struct.unpack('>H', pack[12:14]))

            print('### IP Packet:')
            ip = pack[ETH_LEN:]
            ver_hdl = ip[0:1]
            ver_hdl_dec = struct.unpack('>B', pack[14:14 + 1])
            ver_hdl_hex = binascii.hexlify(ver_hdl)
            print('Version + HDL (dec): %d' % ver_hdl_dec)
            print('Version + HDL (hex): %s' % ver_hdl_hex.decode())
            if ver_hdl_hex == b'45':
                print('Header length is %d' % (5 * 4))
            else:
                print('Addtional header options!')
                sys.exit(1)
            ip_tlen = int.from_bytes(ip[2:4], byteorder='big')
            print('Total length: %d' % ip_tlen)
            proto = binascii.hexlify(ip[9:10]).decode()
            print('Protocol: %s' % proto)
            proto = struct.unpack('>B', ip[9:10])
            print('Protocol (dec): %s' % proto)

            print('### UDP Segment:')
            udp = ip[IHL:]
            print('Source port: ' + binascii.hexlify(udp[0:0 + 2]).decode())
            print('Destination port: ' +
                  binascii.hexlify(udp[2:2 + 2]).decode())
            udp_len_dec = int.from_bytes(udp[4:6], byteorder='big')
            print('Total length (dec): %s' % udp_len_dec)
            print('Checksum: %s' % binascii.hexlify(udp[6:8]).decode())
            udp_plen = udp_len_dec - 8
            print('Payload length (dec): %s' % udp_plen)

            parsed_num += 1
            if parsed_num == pack_num:
                break


if __name__ == "__main__":
    # test_dpkt()
    test_bytearray()
