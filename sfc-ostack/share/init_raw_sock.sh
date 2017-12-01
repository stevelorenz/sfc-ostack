#!/bin/bash

# About: Init script for handling packet with raw sockets
# Email: xianglinks@gmail.com

CTL_IP="192.168.12.10"
CTL_PORT=6666
SUBNET_CIDR="10.0.12.0/32"
SRC_ADDR="10.0.12.4/32"
DST_ADDR="10.0.12.12/32"

# Setup ingress and egress interface
ip link set eth1 up
ip link set eth2 up
# Assign IP via DHCP
dhclient eth1
dhclient eth2

# Remove duplicated routing items
ip route del $SUBNET_CIDR dev eth1
ip route del $SUBNET_CIDR dev eth2

# Add static routes to src and dst
ip route add $SRC_ADDR dev eth1
ip route add $DST_ADDR dev eth2

# Get and run SF program
curl $CTL_IP:8888/fwd_raw_sock.py -o /home/ubuntu/fwd_raw_sock.py
python3 /home/ubuntu/fwd_raw_sock.py > /dev/null 2>&1 &

# Send a ready packet to controller
# MARK: This CAN be done in the SF program
echo -n "SF is ready" > /dev/udp/$CTL_IP/$CTL_PORT
