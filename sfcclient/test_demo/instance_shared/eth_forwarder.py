#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About : A simple Ethernet frame forwarder based on raw sockets
        It only receive all frames

        Use multiprocessing for receiving and forwarding frames

Note  :

Email : xianglinks@gmail.com
"""

import multiprocessing
import socket
import struct
import sys

import netifaces

#############
#  Configs  #
#############

# ingress and egress interface name
INGRESS_IFCE = 'eth1'
EGRESS_IFCE = 'eth2'

TEST_IFCE = 'lo'


###############
#  Forwarder  #
###############

class EthForwarder(object):

    """A simple Ethernet frame forwarder"""

    def __init__(self, ip_proto, ingress_ifce, egress_ifce):
        """Init a new EthForwarder"""
        self.ingress_ifce = ingress_ifce
        self.egress_ifce = egress_ifce
        # parse IP protocols
        if ip_proto.lower() == 'icmp':
            self.ip_proto = socket.IPPROTO_ICMP
        elif ip_proto.lower() == 'udp':
            self.ip_proto = socket.IPPROTO_UDP
        else:
            raise RuntimeError('Unsupported protocol: %s' % ip_proto)
        try:
            # MARK: use raw socket to get the header parts
            self.src_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, self.ip_proto)
            self.dst_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, self.ip_proto)
        except socket.error as msg:
            print('Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
            sys.exit()

    # --- Packet Operation ---

    def _unpack(self, packet):
        """Unpack a IP packet

        :param packet:
        """
        pass

    @staticmethod
    def _get_mac_addr(ifce_name):
        """Get the MAC address of a interface

        :param ifce_name (str)
        :retype: str
        """
        return netifaces.ifaddresses(ifce_name)[netifaces.AF_LINK][0]['addr']

    @staticmethod
    def _print_frame(frame, handler='console'):
        """Print infos of a frame

        :param frame:
        :param handler:
        """
        pass

    def cleanup(self):
        """Cleanups"""
        if self.src_sock:
            self.src_sock.close()

    def run(self):
        """Run Ethernet forwarder"""
        print('Start forwarding Ethernet frames from %s to %s'
              % (self.ingress_ifce, self.egress_ifce))


##########
#  Test  #
##########

def test():
    """Run common tests"""
    print('# Run tests for eth_forwarder...')
    eth_fwdr = EthForwarder('udp', INGRESS_IFCE, EGRESS_IFCE)
    try:
        while True:
            pkt = eth_fwdr.src_sock.recvfrom(65565)
            print(pkt)
    except KeyboardInterrupt:
        eth_fwdr.cleanup()
        sys.exit()


if __name__ == "__main__":
    test()
