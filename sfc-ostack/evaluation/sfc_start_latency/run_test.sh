#!/bin/bash
# About: Run chain creation latency tests
# Email: xianglinks@gmail.com

MIN_SF_NUM=1
MAX_SF_NUM=1
TEST_ROUND=1
ADD_ROUND=2
MODE=0

DST_IP=10.0.0.7
DST_PORT=9999

# Floating IPs
SRC_FIP=192.168.100.105
DST_FIP=192.168.100.102

SSH_PKEY="/home/zuo/sfc_ostack_test/sfc_test.pem"

SEND_INTERVAL=1
timer_srv_cmd="nohup python3 /home/ubuntu/ctime_timer.py -c $DST_IP:$DST_PORT --send_interval $SEND_INTERVAL --payload_len 1 > /dev/null 2>&1 &"

##############
#  Run Test  #
##############

echo "Run chain cleanups"
python3 ./test_stime.py "$MIN_SF_NUM" "$MAX_SF_NUM" "$DST_IP:$DST_PORT" "$DST_FIP" -r "$TEST_ROUND" --full_clean > /dev/null 2>&1

# Run a simple HTTP server for file sharing among SF instances
python3 -m http.server 8888 > /dev/null 2>&1 &

# Copy and run ctimer on src, dst instances
scp -i "$SSH_PKEY" ./ctime_timer.py "ubuntu@$SRC_FIP":~/
scp -i "$SSH_PKEY" ./ctime_timer.py "ubuntu@$DST_FIP":~/

echo "[DEBUG] Restart ctime_timer client on src instance"
ssh -i "$SSH_PKEY" "ubuntu@$SRC_FIP" "pkill -f python3"
# Expand by local host
echo "$timer_srv_cmd" | xargs -I {} ssh -i "$SSH_PKEY" "ubuntu@$SRC_FIP" {}

echo "Run chain creation latency tests"
python3 ./test_stime.py "$MIN_SF_NUM" "$MAX_SF_NUM" "$DST_IP:$DST_PORT" "$DST_FIP" -r "$TEST_ROUND" -m "$MODE" --add_round "$ADD_ROUND"

# Copy all CSV data
scp -i "$SSH_PKEY" "ubuntu@$DST_FIP":/home/ubuntu/*.csv ./

echo "Run cleanups"
pgrep -f 'python3 -m http' | xargs kill
ssh -i "$SSH_PKEY" "ubuntu@$SRC_FIP" "pkill -f python3"
ssh -i "$SSH_PKEY" "ubuntu@$DST_FIP" "pkill -f python3"
python3 ./test_stime.py "$MIN_SF_NUM" "$MAX_SF_NUM" "$DST_IP:$DST_PORT" "$DST_FIP" -r "$TEST_ROUND" --full_clean > /dev/null 2>&1
