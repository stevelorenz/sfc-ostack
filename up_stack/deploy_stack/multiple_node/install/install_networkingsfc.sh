#!/bin/bash
# About: Install and configure Neutron networking-sfc extension

neutron_conf=/etc/neutron/neutron.conf
neutron_ml2_conf=/etc/neutron/plugins/ml2/openvswitch_agent.ini

function print_help() {
    echo ""
    echo "About: Install and configure Neutron networking-sfc extension"
    echo "Usage: sudo bash ./install_networkingsfc.sh node_type"
}

function install_networking_sfc() {
    echo "Install networking-sfc with pip, release: $1, version: $2"
    pip install -c https://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?h="$1" networking-sfc=="$2"
}

if [[ "$1" == "controller" ]]; then
    echo "# Setup networking-sfc on controller node"
    install_networking_sfc "stable/pike" "5.0.0"
    if [[ -e $neutron_conf ]] || [[ -e $neutron_ml2_conf ]]; then
        echo "  Config networking-sfc plugin"
        crudini --set $neutron_conf DEFAULT service_plugins router,flow_classifier,sfc
        crudini --set $neutron_conf sfc drivers ovs
        crudini --set $neutron_conf flow_classifier drivers ovs
        echo "  Config neutron database"
        neutron-db-manage --subproject networking-sfc upgrade head
        echo "  Restart neutron server"
        systemctl restart neutron-server
        sleep 3
        systemctl | grep neutron-server
        echo "  Installation finished"
    else
        echo "[ERROR] Missing Neutron config file"
    fi

elif [[ "$1" == "compute" ]]; then
    echo "# Setup networking-sfc on compute node"
    install_networking_sfc "stable/pike" "5.0.0"
    if [[ -e $neutron_conf ]] || [[ -e $neutron_ml2_conf ]]; then
        echo "  Config networking-sfc plugin"
        crudini --set $neutron_ml2_conf agent extensions sfc
        echo "  Config neutron database"
        neutron-db-manage --subproject networking-sfc upgrade head
        echo "  Restart neutron ovs agent"
        systemctl restart neutron-openvswitch-agent
        sleep 3
        systemctl | grep neutron-openvswitch-agent
        echo "  Installation finished"
    else
        echo "[ERROR] Missing Neutron config file"
    fi

else
    echo "Unknown node type! Use controller or compute as option."
    print_help
    exit
fi
