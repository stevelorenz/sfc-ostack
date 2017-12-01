#!/bin/bash
# About: (Depreciated!) Init script for OpenVswitch forwarding
#        Use raw socket forwarding instead
# Issue:
#    - OVS bridge IP is not in the neutron port's database, ARP requests are filtered by neutron firewall
#    - OVS bridge does not handle backwards traffic in the chain, which sometime happens during tests

# Email: xianglinks@gmail.com

CTL_IP="192.168.12.10"
CTL_PORT=6666

# Setup ingress and egress interface
ip link set eth1 up
ip link set eth2 up

# Source and destination instance IP
SRC_IP=10.0.0.1
DST_IP=10.0.0.2

# SF program SHOULD read and send chained packets from BRIDGE_IP
BRIDGE_IP=192.168.0.1
# The source IP of ingress packets is modified as "fake" IP before forwarding to
# the OVS local port. According to the test, this step is needed for
# successfully reading packets from local port with common socket.
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

####################
#  Run SF Program  #
####################

# Distribute the SF program by any other method before running, for example via HTTP server
curl 192.168.100.1:8888/udp_forwarding.py -o /home/ubuntu/udp_forwarding.py
python3 /home/ubuntu/udp_forwarding.py > /dev/null 2>&1 &

# Send a ready packet to controller
# MARK: This CAN be done in the SF program
echo -n "SF is ready" > /dev/udp/$CTL_IP/$CTL_PORT
