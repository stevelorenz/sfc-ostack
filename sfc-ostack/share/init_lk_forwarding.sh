#!/bin/bash

# About: Init script for Linux kernel forwarding
# Email: xianglinks@gmail.com

CTL_IP="192.168.12.10"
CTL_PORT=6666
SUBNET_CIDR="10.0.12.0/24"
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

# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# Send a ready packet to controller
echo -n "SF is ready" > /dev/udp/$CTL_IP/$CTL_PORT
