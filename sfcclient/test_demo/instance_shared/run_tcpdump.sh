#!/bin/bash
# About: Use tcpdump to capture UDP packets from specific interface

tcpdump -e -i eth0 -nnXSs 0 udp > cap_data.txt
