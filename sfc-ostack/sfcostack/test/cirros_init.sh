#!/bin/bash
# About: sfc-ostack init configs for cirros
#        Use cloud-init via user-data
#
# Email: xianglinks@gmail.com

# Setup ingress and egress interface
ip link set eth1 up
ip link set eth2 up
/sbin/cirros-dhcpc up eth1
/sbin/cirros-dhcpc up eth2

# Delete duplicated routes
ip route del 10.0.0.0/24 dev eth1
ip route del 10.0.0.0/24 dev eth2
