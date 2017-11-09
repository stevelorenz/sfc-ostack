#!/bin/bash
# About: Init script for Linux kernel forwarding
# Email: xianglinks@gmail.com

# Setup ingress and egress interface
ip link set eth1 up
ip link set eth2 up
# Assign IP
dhclient eth1
dhclient eth2

# Remove duplicated routing items
ip route del 10.0.0.0/24 dev eth1
ip route del 10.0.0.0/24 dev eth2

# Add static routes to src and dst
ip route add 10.0.0.1/32 dev eth1
ip route add 10.0.0.2/32 dev eth2

# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward
