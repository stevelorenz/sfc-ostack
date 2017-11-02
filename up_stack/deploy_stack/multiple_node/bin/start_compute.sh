#!/bin/bash
# About: Start OpenStack services on compute node
# Email: xianglinks@gmail.com

function notify() {
    local len=$((${#1}+2))
    printf "\n+"
    printf -- "-%.0s" $(seq 1 $len)
    printf "+\n| $1 |\n+"
    printf -- "-%.0s" $(seq 1 $len)
    printf "+\n\n"
}

# Restart a array of services
function restart_srv_arr() {
    arr=("$@")
    for srv in "${arr[@]}"; do
        echo "* Restart $srv"
        systemctl restart "$srv"
        sleep 3
        #systemctl status "$srv"
        systemctl | grep "$srv"
        sleep 3
    done
}

notify "Start OpenStack services on compute node"

echo "### Start nova services ###"
declare -a srv_arr=(
"nova-compute"
)
restart_srv_arr "${srv_arr[@]}"

echo "### Start neutron services ###"
declare -a srv_arr=(
"neutron-openvswitch-agent"
)
restart_srv_arr "${srv_arr[@]}"
