#!/bin/bash
# About: sfc-ostack init configs for ubuntu-cloud
#        Use cloud-init via user-data
#
# Email: xianglinks@gmail.com

# Setup ingress and egress interface
ip link set eth1 up
ip link set eth2 up
dhclient eth1
dhclient eth2

# Delete duplicated routes
ip route del 10.0.0.0/24 dev eth1
ip route del 10.0.0.0/24 dev eth2

# Enable IP forwarding
# echo 1 > /proc/sys/net/ipv4/ip_forward
