#!/bin/bash
# About: Init script for Linux kernel forwarding
#
# Email: xianglinks@gmail.com

# Setup ingress and egress interface
ip link set eth1 up
ip link set eth2 up
dhclient eth1
dhclient eth2

ip route del 10.0.0.0/24 dev eth1
ip route del 10.0.0.0/24 dev eth2

# Add static routes
ip route add 10.0.0.3 dev eth1
ip route add 10.0.0.10 dev eth2

# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward
