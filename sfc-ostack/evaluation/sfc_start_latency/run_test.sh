#!/bin/bash
# About: Run chain creation latency tests
# Email: xianglinks@gmail.com

################
#  Test Paras  #
################

MIN_SF_NUM=1
MAX_SF_NUM=1
TEST_ROUND=5
ADD_ROUND=0
MODE=0
SEND_INTERVAL=0.001

# Fix IP and port
DST_IP=10.0.0.7
DST_PORT=9999
# Floating IPs
SRC_FIP=192.168.100.105
DST_FIP=192.168.100.102
SSH_PKEY="/home/zuo/sfc_ostack_test/sfc_test.pem"

timer_srv_cmd="nohup python3 /home/ubuntu/ctime_timer.py -c $DST_IP:$DST_PORT --send_interval $SEND_INTERVAL --payload_len 1 -l ERROR > /dev/null 2>&1 &"

##############
#  Run Test  #
##############

echo "# Run chain cleanups"
python3 ./test_stime.py "$MIN_SF_NUM" "$MAX_SF_NUM" "$DST_IP:$DST_PORT" "$DST_FIP" -r "$TEST_ROUND" --clean > /dev/null 2>&1

# Run a simple HTTP server for file sharing among SF instances
echo "# Run HTTP server on port 8888"
python3 -m http.server 8888 > /dev/null 2>&1 &

# Copy and run ctimer on src, dst instances
echo "# Copy ctime_timer to src and dst server"
scp -i "$SSH_PKEY" ./ctime_timer.py "ubuntu@$SRC_FIP":~/
scp -i "$SSH_PKEY" ./ctime_timer.py "ubuntu@$DST_FIP":~/

echo "# Run ntp client on src and dst server"
scp -i "$SSH_PKEY" ./init_ntp_client.sh "ubuntu@$SRC_FIP":~/
scp -i "$SSH_PKEY" ./init_ntp_client.sh "ubuntu@$DST_FIP":~/
ssh -i "$SSH_PKEY" "ubuntu@$SRC_FIP" "sudo sh ./init_ntp_client.sh" > /dev/null 2>&1
ssh -i "$SSH_PKEY" "ubuntu@$DST_FIP" "sudo sh ./init_ntp_client.sh" > /dev/null 2>&1
echo "# Wait some time for NTP synchronization..."
sleep 30

echo "# Restart ctime_timer client on src instance"
ssh -i "$SSH_PKEY" "ubuntu@$SRC_FIP" "killall python3"
# Expand by local host
echo "$timer_srv_cmd" | xargs -I {} ssh -i "$SSH_PKEY" "ubuntu@$SRC_FIP" {}

echo "# Run chain start latency tests"
python3 ./test_stime.py "$MIN_SF_NUM" "$MAX_SF_NUM" "$DST_IP:$DST_PORT" "$DST_FIP" -r "$TEST_ROUND" -m "$MODE" --add_round "$ADD_ROUND"

echo "# Run cleanups"
pgrep -f 'python3 -m http' | xargs kill
echo "# Kill ctime_timer on src and dst server"
ssh -i "$SSH_PKEY" "ubuntu@$SRC_FIP" "killall python3"
ssh -i "$SSH_PKEY" "ubuntu@$DST_FIP" "killall python3"
python3 ./test_stime.py "$MIN_SF_NUM" "$MAX_SF_NUM" "$DST_IP:$DST_PORT" "$DST_FIP" -r "$TEST_ROUND" --clean > /dev/null 2>&1

# Copy all CSV data
echo "# Copy CSV data from dst server"
scp -i "$SSH_PKEY" "ubuntu@$DST_FIP":/home/ubuntu/*.csv ./
