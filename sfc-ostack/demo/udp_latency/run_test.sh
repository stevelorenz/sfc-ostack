#!/bin/bash
# About: Run latency measurement

#####################
#  Test Parameters  #
#####################

SERVER_ADDR="192.168.100.200:9999"

SFC_MGR=./sfc_mgr.py

NUM_PACKETS=10000
#NUM_PACKETS=10
SEND_RATE=1000 # byte/s
PAYLOAD_LEN=512 # byte

MAX_FC_NUM=9

echo "Maximal $MAX_FC_NUM of chain nodes"

# Create SFC
for (( srv_num = 5; srv_num <= $MAX_FC_NUM; srv_num++ )); do
    echo "Number of FC servers: $srv_num"
    python "$SFC_MGR" c "$srv_num"
    # Immer langsamer bitte...
    sleep 15
    # Run UDP Client
    python ./udp_latency.py -c "$SERVER_ADDR" --n_packets "$NUM_PACKETS" --payload_len "$PAYLOAD_LEN" \
        --send_rate "$SEND_RATE" --output_file "$NUM_PACKETS-$SEND_RATE-$PAYLOAD_LEN-$srv_num.csv"
    sleep 15
    python "$SFC_MGR" d "$srv_num"
    sleep 5
    ~/bin/dbxcli-linux-amd64 put "./$NUM_PACKETS-$SEND_RATE-$PAYLOAD_LEN-$srv_num.csv"
done
