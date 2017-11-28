#!/bin/bash
#
# About: Install and config NTP client
#        Use chrony

apt -y install chrony

cat >/etc/chrony/chrony.conf <<EOL

server 192.168.100.1 iburst

# Time-service des ZIH
# server time.zih.tu-dresden.de iburst

keyfile /etc/chrony/chrony.keys

dumpdir /var/lib/chrony
driftfile /var/lib/chrony/chrony.drif

EOL

# Restart chrony daemon
service chrony restart
