#!/bin/bash
# About: Forwarding with OpenVSwitch
# Email: xianglinks@gmail.com

# MARK: The IP address SHOULD not be changed
SRC_IP=192.168.100.1
DST_IP=10.0.0.7

# Setup ingress and egress ifce
ip link set eth1 up
# dhclient eth1

INGRESS_IP_CIDR=$(ip -o addr | grep 'eth0' | grep 'inet ' | awk '{print $4}')
EGRESS_IP_CIDR=$(ip -o addr | grep 'eth1' | grep 'inet ' | awk '{print $4}')

# Move ingress IP to the bridge
ovs-vsctl add-br br0
ip addr flush dev eth0
ip addr add $INGRESS_IP_CIDR dev br0

###############
#  Add Ports  #
###############

sudo ovs-vsctl add-port br0 eth0
sudo ovs-vsctl add-port br0 eth1
sudo ovs-ofctl mod-port br0 1 no-flood
sudo ovs-ofctl mod-port br0 2 no-flood

###############
#  Add Flows  #
###############

#sudo ovs-ofctl add-flow "$BG_NAME" "in_port=1 actions=output:2"
# modify the source and destination MAC address
#sudo ovs-ofctl add-flow "$BG_NAME" "in_port=1 actions=mod_dl_src:$IG_IFCE_MAC,mod_dl_dst:$EG_IFCE_MAC,output:2"

# Change IP address before sending
