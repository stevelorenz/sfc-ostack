#!/bin/bash

# About: Run UDP latency measurements
# Email: xianglinks@gmail.com

#####################
#  Test Parameters  #
#####################

# Address of UDP echo server
SERVER_ADDR="192.168.100.200:9999"

# SFC manager
SFC_MGR=./sfc_mgr.py

# UDP client parameters
NUM_PACKETS=10000
SEND_RATE=1000 # byte/s
PAYLOAD_LEN=512 # byte

# Maximal number of SF instances
MAX_SF_NUM=2

####################
#  Test Functions  #
####################

function lk_forwarding_test {
    for (( srv_num = 1; srv_num <= $MAX_SF_NUM; srv_num++ )); do
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
        # Upload result to Dropbox
        ~/bin/dbxcli-linux-amd64 put "./$NUM_PACKETS-$SEND_RATE-$PAYLOAD_LEN-$srv_num.csv"
    done
}

# MARK: TODO Rewrite test functions in python
function py_forwarding_test {
    for (( srv_num = 1; srv_num <= $MAX_SF_NUM; srv_num++ )); do
        echo "Number of FC servers: $srv_num"
        python "$SFC_MGR" c "$srv_num"
        # Immer langsamer bitte...
        sleep 15
        # Copy forwarding program to all instances

        # Run forwarding program

        # Run UDP Client
        python ./udp_latency.py -c "$SERVER_ADDR" --n_packets "$NUM_PACKETS" --payload_len "$PAYLOAD_LEN" \
            --send_rate "$SEND_RATE" --output_file "$NUM_PACKETS-$SEND_RATE-$PAYLOAD_LEN-$srv_num.csv"
        sleep 10
        python "$SFC_MGR" d "$srv_num"
        sleep 5
        # Upload result to Dropbox
        ~/bin/dbxcli-linux-amd64 put "./$NUM_PACKETS-$SEND_RATE-$PAYLOAD_LEN-$srv_num.csv"
    done

}

echo "Maximal $MAX_SF_NUM of SF nodes."

#echo "Run lk_forwarding_test"
#lk_forwarding_test

echo "Run py_forwarding_test"
#py_forwarding_test
