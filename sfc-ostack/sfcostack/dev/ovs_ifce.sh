#!/bin/bash

##########
#  IFCE  #
##########


ovs-vsctl add-br br0

# Dump ingress ifce IP
ip addr flush eth0


# Add static routes
