#!/bin/bash
# About: Start OpenStack services on controller node
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

notify "Start OpenStack services on controller node"

echo "### Start base services ###"
declare -a srv_arr=(
"mysql"
"rabbitmq-server"
"memcached"
"etcd"
"apache2"
)
restart_srv_arr "${srv_arr[@]}"

echo "### Start glance services ###"
declare -a srv_arr=(
"glance-registry"
"glance-api"
)
restart_srv_arr "${srv_arr[@]}"

echo "### Start nova services ###"
declare -a srv_arr=(
"nova-api"
"nova-consoleauth"
"nova-scheduler"
"nova-conductor"
"nova-novncproxy"
)
restart_srv_arr "${srv_arr[@]}"

echo "### Start heat services ###"
declare -a srv_arr=(
"heat-api"
"heat-api-cfn"
"heat-engine"
)
restart_srv_arr "${srv_arr[@]}"

echo "### TODO: Config external bridge ###"

echo "### Start neutron services ###"
declare -a srv_arr=(
"neutron-server"
"neutron-openvswitch-agent"
"neutron-l3-agent"
"neutron-dhcp-agent"
"neutron-metadata-agent"
)
restart_srv_arr "${srv_arr[@]}"
