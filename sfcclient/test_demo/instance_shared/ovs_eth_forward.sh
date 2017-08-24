#!/bin/bash
# About: Use OVS for chained-interface forwarding
# Email: xianglinks@gmail.com

BG_NAME='br0'

##############
#  Iterface  #
##############

# ingress and egress ifce
IG_IFCE='eth1'
EG_IFCE='eth2'

echo "# Use OVS for interface forwarding, bridge name: $BG_NAME"

IG_IFCE_MAC=$(cat /sys/class/net/$IG_IFCE/address)
EG_IFCE_MAC=$(cat /sys/class/net/$EG_IFCE/address)
echo "## MAC of the ingress interface: $IG_IFCE_MAC"
echo "## MAC of the egress interface: $EG_IFCE_MAC"

#########
#  OVS  #
#########

# Run OVS in kernel mod

# Create a bridge
sudo ovs-vsctl add-br "$BG_NAME"

# Bind interfaces
sudo ovs-vsctl add-port "$BG_NAME" "$IG_IFCE"
sudo ovs-vsctl add-port "$BG_NAME" "$EG_IFCE"

# No flooding on both ingress- and egress ports
sudo ovs-ofctl mod-port "$BG_NAME" 1 no-flood
sudo ovs-ofctl mod-port "$BG_NAME" 2 no-flood

# --- Add Flows ---

#sudo ovs-ofctl add-flow "$BG_NAME" "in_port=1 actions=output:2"

# modify the source and destination MAC address
#sudo ovs-ofctl add-flow "$BG_NAME" "in_port=1 actions=output:2,mod_dl_src:$IG_IFCE_MAC,mod_dl_dst:$EG_IFCE_MAC"

echo "# OVS with port forwarding is setup."
