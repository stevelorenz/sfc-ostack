#!/bin/bash
# ------------------------------------------------
# About: Init script for python forwarding, V2
#
# Email: xianglinks@gmail.com
# ------------------------------------------------

# SFC source and destination address
SRC_ADDR=10.0.0.1/24
DST_ADDR=10.0.0.2/24

# Setup ingress and egress interface
ip link set eth1 up
ip link set eth2 up

# Add addr of egress ifce to the forwarding bridge
dhclient eth2
EGRESS_ADDR=$(ip -o addr show eth2 | grep 'inet ' | awk '{print $4}')
BRIDGE_ADDR=$EGRESS_ADDR
ip addr flush eth2

ovs-vsctl add-br br0
ip addr add "$BRIDGE_ADDR" dev br0

# Disable ifce checksum offloading
ethtool --offload br0 rx off tx off
ethtool --offload eth1 rx off tx off
ethtool --offload eth2 rx off tx off

# MAC addr of the bridge interface
BRIDGE_MAC=$(cat /sys/class/net/br0/address)
# EGRESS_MAC=$(cat /sys/class/net/eth2/address)

###############
#  Add Ports  #
###############

ovs-vsctl add-port br0 eth1
ovs-vsctl add-port br0 eth2

# Disable port flooding
ovs-ofctl mod-port br0 1 no-flood
ovs-ofctl mod-port br0 2 no-flood

###############
#  Add Flows  #
###############

# Route ingress packets to OVS LOCAL port
ovs-ofctl add-flow br0 "in_port=1 actions=mod_dl_dst:$BRIDGE_MAC,mod_nw_dst:$BRIDGE_ADDR,LOCAL"

# Route packets from LOCAL port to egress port
ip route add $DST_ADDR dev br0
ovs-ofctl add-flow br0 "in_port=local actions=mod_nw_src:$SRC_ADDR,mod_nw_dst:$DST_ADDR,output:2"

####################
#  Run SF Program  #
####################

curl 192.168.100.1:8888/udp_forwarding.py -o /home/ubuntu/udp_forwarding.py
python3 /home/ubuntu/udp_forwarding.py > /dev/null 2>&1 &
