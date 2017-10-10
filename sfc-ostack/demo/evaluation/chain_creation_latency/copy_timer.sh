#!/bin/bash
# About: Copy timer program on remote instances

SRC_FIP="192.168.100.200"
DST_FIP="192.168.100.205"
SSH_PKEY='/home/zuo/sfc_ostack_test/sfc_test.pem'

scp -i "$SSH_PKEY" ./ctime_timer.py "ubuntu@$SRC_FIP":~/
scp -i "$SSH_PKEY" ./ctime_timer.py "ubuntu@$DST_FIP":~/
