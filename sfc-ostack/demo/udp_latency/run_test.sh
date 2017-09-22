#!/bin/bash
# About: Run latency measurement

#####################
#  Test Parameters  #
#####################

SERVER_ADDR="192.168.100.200:9999"

SFC_MGR=./sfc_mgr.py

NUM_PACKETS=10000
SEND_RATE=1000 # byte/s
PAYLOAD_LEN=512 # byte

MAX_FC_NUM=2

# Create SFC
for (( srv_num = 1; srv_num <= $MAX_FC_NUM; srv_num++ )); do
    echo "Number of FC servers: $srv_num"
    python "$SFC_MGR" c "$srv_num"
    # Immer langsamer bitte...
    sleep 10
    # Run UDP Client
    python ./udp_latency.py -c "$SERVER_ADDR" --n_packets "$NUM_PACKETS" --payload_len "$PAYLOAD_LEN" \
        --send_rate "$SEND_RATE" --output_file "$srv_num"
    sleep 10
    python "$SFC_MGR" d "$srv_num"
done
