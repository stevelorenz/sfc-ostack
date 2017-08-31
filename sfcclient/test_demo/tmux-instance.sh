#!/bin/bash
#
# About: Create a new Tmux session for remote instances

SESSION="ostack-sfc-test"

KEY_FILE="./test.pem"

tmux new-session -d -s $SESSION

readarray ips < ./remote_instance.txt

win_idx=2
for ip in "${ips[@]}"
do
    tmux new-window -t "$SESSION:$win_idx"
    tmux send-keys -t "$SESSION:$win_idx" "ssh -o \"StrictHostKeyChecking no\" -i $KEY_FILE ubuntu@$ip" C-m
    let "win_idx++"
done
