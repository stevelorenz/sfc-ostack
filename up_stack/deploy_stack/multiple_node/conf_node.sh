#!/bin/bash
# About: Basic configuration for controller and compute node

##########
#  Conf  #
##########

path_hosts=/etc/hosts
path_hostname=/etc/hostname
path_interfaces=/etc/network/interfaces

controller_ifce_1=eno1

int_net_dhcp_ifce=eno1
int_net_dhcp_server="192.168.13.1/24"
int_net_dhcp_range="$int_net_dhcp_ifce,192.168.13.10,192.168.13.20,12h"
int_net_netmask=255.255.255.0

mgr_net_subnet=192.168.12.0/24
mgr_net_netmask=255.255.255.0

# NTP server on controller node
ntp_server_ip=192.168.12.10

##############
#  Function  #
##############

function print_help() {
    echo ""
    usage="$(basename "$0") node_type operation"
    echo "Usage: $usage" >&2
    echo "[WARN] Run with sudo or root"
    echo "  node_type: controller, compute"
    echo "  controller operation: network, ntp_server, dnsmasq"
    echo "  computer operation: network, ntp_client"
}

function conf_controller_network() {
    echo "# Config networking on controller node."
    echo "## Config interfaces in $path_interfaces"
    cat >"$path_interfaces" << EOL
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

source /etc/network/interfaces.d/*

auto lo
iface lo inet loopback

# Management and external network
auto enp5s0
iface enp5s0 inet dhcp

# Internal data network
auto eno1
iface eno1 inet static
address $IP_INT_DHCP_SERVER
netmask $NETMASK
EOL
    echo "## Config hostname and hosts"
    echo "## Restart networking service"
    service networking restart
}

function conf_compute_network() {
    echo "# Config networking on compute node"
    echo "## Config interfaces in $path_interfaces"
    cat >"$path_interfaces" << EOL
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

source /etc/network/interfaces.d/*

auto lo
iface lo inet loopback

# Management network
auto eno1
iface eno1 inet dhcp

# Internal data network
# MARK: Change the iterface name here properly
#       comnets-ostack-1 has two NICs, named enp5s0 and enp4s0
#       other two machines have only one NIC, default named enp2s0
auto int_iface
iface int_iface inet dhcp
EOL
}

function conf_ntp_server() {
    echo "# Config chrony NTP server"
    systemctl disable systemd-timesyncd.service
    apt -y install chrony
    cat >/etc/chrony/chrony.conf << EOL
# Allow host on this subnet to use NTP server
allow $mgr_net_subnet

# Remote NTP server
server time.zih.tu-dresden.de iburst

keyfile /etc/chrony/chrony.keys

dumpdir /var/lib/chrony
driftfile /var/lib/chrony/chrony.drif
EOL
    service chrony restart
    echo "## NTP sources"
    chronyc sources
}

function conf_ntp_client() {
    echo "# Config chrony NTP client"
    systemctl disable systemd-timesyncd.service
    apt -y install chrony
    cat >/etc/chrony/chrony.conf << EOL
# Remote NTP server
server $ntp_server_ip iburst

keyfile /etc/chrony/chrony.keys

dumpdir /var/lib/chrony
driftfile /var/lib/chrony/chrony.drif
EOL
    service chrony restart
    echo "## NTP sources"
    chronyc sources
}

function conf_dnsmasq() {
    echo "# Config dnsmasq on controller"
    cat >/etc/dnsmasq.conf << EOL
# About: Configuration file for dnsmasq.
#        dnsmasq is used for DHCP and DNS services in the OpenStack data network
# Remote NTP server

# If you want dnsmasq to listen for DHCP and DNS requests only on
# specified interfaces (and the loopback) give the name of the
# interface (eg eth0) here.
interface=$int_net_dhcp_ifce
dhcp-range=$int_net_dhcp_range
EOL
    echo "## Restart dnsmasq daemon"
    sudo systemctl restart dnsmasq.service
}

##########
#  Main  #
##########

if [[ ($1 == "-h") || ($1 == "--help") ]]; then
    print_help
    exit
fi

if [[ $1 == "controller" ]]; then
    if [[ $2 == "dnsmasq" ]]; then
        conf_dnsmasq
    elif [[ $2 == "ntp_server" ]]; then
        conf_ntp_server
    elif [[ $2 == "network" ]]; then
        conf_controller_network
    else
        print_help
        echo "[ERROR] Unknown controller node operation!"
        exit
    fi
elif [[ $1 == "compute" ]]; then
    if [[ $2 == "ntp_client" ]]; then
        conf_ntp_client
    elif [[ $2 == "network" ]]; then
        conf_compute_network
    else
        echo "[ERROR] Unknown compute node operation!"
        print_help
        exit
    fi
else
    echo "[ERROR] Unknown node type!"
    print_help
    exit
fi
