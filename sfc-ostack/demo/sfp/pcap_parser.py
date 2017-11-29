#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About : Parse PCAP file of kernerl forwarded packet
Email : xianglinks@gmail.com
"""

import binascii

import dpkt

if __name__ == "__main__":
    pack_num = 1
    # Load and parser pcap file
    with open('./lk_out.pcap', 'rb') as pcap_f:
        parsed_num = 0
        pcap = dpkt.pcap.Reader(pcap_f)
        for ts, buf in pcap:
            print('# TS: %f, len: %d' % (ts, len(buf)))
            eth = dpkt.ethernet.Ethernet(buf)

            print('## Ethernet Frame:')

            print('## IP Packet:')
            ip = eth.data
            print('packet len: %d' % ip.len)
            print('header len: %d' % ip.hl)
            print('src_ip: %s, dst_ip: %s' % (ip.src, ip.dst))
            print('checksum: %x' % ip.sum)

            print('## UDP Segment:')
            udp = ip.data
            print('src_port: %d' % udp.sport)
            print('dst_port: %d' % udp.dport)
            print('checksum: %x' % udp.sum)
            print('payload: %s' % binascii.hexlify(udp.data).decode())

            parsed_num += 1
            if parsed_num == pack_num:
                break
