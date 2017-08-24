#!/bin/bash
#
# About: Create a new Tmux session for remote instances

### Config Options ###

SESSION="ostack-sfc-test"

# Host and floating IPs
SRC_VM="ubuntu@192.168.0.209"
DST_VM="ubuntu@192.168.0.205"
CHN_VM="ubuntu@192.168.0.200"

# SSH Key
KEY_FILE="./test.pem"

### End of Config Options ###

# Create a new tmux session
tmux new-session -d -s $SESSION

tmux rename-window -t $SESSION:1 src_vm
tmux send-keys -t $SESSION:1 "ssh -i $KEY_FILE $SRC_VM" C-m

tmux new-window -t $SESSION:2
tmux rename-window -t $SESSION:2 dst_vm
tmux send-keys -t $SESSION:2 "ssh -i $KEY_FILE $DST_VM" C-m

tmux new-window -t $SESSION:3
tmux rename-window -t $SESSION:3 chain_vm
tmux send-keys -t $SESSION:3 "ssh -i $KEY_FILE $CHN_VM" C-m

# Attach tmux client to the new server session
tmux attach -t $SESSION
