#!/bin/bash
# About: Init script for python forwarding
#
# Email: xianglinks@gmail.com

# Setup ingress and egress interface
ip link set eth1 up
ip link set eth2 up

SRC_IP=10.0.0.3
DST_IP=10.0.0.10

BRIDGE_IP=192.168.0.1
FAKE_INGRESS_IP=192.168.0.100

# Move ingress IP to the bridge
ovs-vsctl add-br br0
# MARK: DO NOT forget to add the MASK
ip addr add "$BRIDGE_IP/24" dev br0

# Disable ifce checksum offloading
ethtool --offload br0 rx off tx off
ethtool --offload eth1 rx off tx off
ethtool --offload eth2 rx off tx off

# MAC addr of the bridge interface
BRIDGE_MAC=$(cat /sys/class/net/br0/address)

###############
#  Add Ports  #
###############

ovs-vsctl add-port br0 eth1
ovs-vsctl add-port br0 eth2

# Disable flooding to avoid looping
ovs-ofctl mod-port br0 1 no-flood
ovs-ofctl mod-port br0 2 no-flood

###############
#  Add Flows  #
###############

# Route ingress packets to OVS LOCAL port
ovs-ofctl add-flow br0 "in_port=1 actions=mod_dl_dst:$BRIDGE_MAC,mod_nw_src:$FAKE_INGRESS_IP,mod_nw_dst:$BRIDGE_IP,LOCAL"

# Route packets from LOCAL port to egress port
ip route add $DST_IP dev br0
ovs-ofctl add-flow br0 "in_port=local actions=mod_nw_src:$SRC_IP,mod_nw_dst:$DST_IP,output:2"
