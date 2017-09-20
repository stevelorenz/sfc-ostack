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
