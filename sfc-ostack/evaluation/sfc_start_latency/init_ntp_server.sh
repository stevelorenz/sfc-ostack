#!/bin/bash
#
# About: Install and config NTP server
#        Use chrony
#
# MARK :  Run this on the control node which has br-ex
#         The 123 port need to be open for client access

apt -y install chrony

cat >/etc/chrony/chrony.conf <<EOL

# Allow host on this subnet to use NTP server
# The range of floating IPs
allow 192.168.100.0/24

keyfile /etc/chrony/chrony.keys

dumpdir /var/lib/chrony
driftfile /var/lib/chrony/chrony.drif

EOL

# Restart chrony daemon
service chrony restart
