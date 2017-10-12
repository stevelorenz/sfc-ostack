#!/bin/bash
# About: Run chain creation latency tests
# Email: xianglinks@gmail.com


MIN_SF_NUM=1
MAX_SF_NUM=1
TEST_ROUND=3

SRC_FIP=192.168.100.200
DST_FIP=192.168.100.205

SSH_PKEY="/home/zuo/sfc_ostack_test/sfc_test.pem"

# Run a simple HTTP server for file sharing among SF instances
python3 -m http.server 8888 > /dev/null 2>&1 &

# Copy and run ctimer on src,dst instances
scp -i "$SSH_PKEY" ./ctime_timer.py "ubuntu@$SRC_FIP":~/
scp -i "$SSH_PKEY" ./ctime_timer.py "ubuntu@$DST_FIP":~/

echo "[DEBUG] Restart ctime_timer client on src instance"
ssh -i "$SSH_PKEY" "ubuntu@$SRC_FIP" "pkill -f python3"
ssh -i "$SSH_PKEY" "ubuntu@$SRC_FIP" "nohup python3 /home/ubuntu/ctime_timer.py -c 10.0.0.10:9999 --send_interval 0.001 --payload_len 1 > /dev/null 2>&1 &"

# --- Run ccl tests
echo "Run chain creation latency tests"
python3 ./run_test_pm.py "$MIN_SF_NUM" "$MAX_SF_NUM" 10.0.0.10:9999 192.168.100.205 -r "$TEST_ROUND"

# --- Copy Data
scp -i "$SSH_PKEY" "ubuntu@$DST_FIP":/home/ubuntu/*.csv ./

# --- Cleanups
echo "Run cleanups"
pgrep -f 'python3 -m http' | xargs kill
ssh -i "$SSH_PKEY" "ubuntu@$SRC_FIP" "pkill -f python3"
ssh -i "$SSH_PKEY" "ubuntu@$DST_FIP" "pkill -f python3"
