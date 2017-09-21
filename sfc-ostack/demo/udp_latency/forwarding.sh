#!/bin/bash
# About: Forwarding
#
# Email: xianglinks@gmail.com

# Setup ingress and egress interface
ip link set eth1 up
dhclient eth1

ip route del 10.0.0.0/24 dev eth1

# Add static routes
ip route add 10.0.0.7 dev eth1

# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward
