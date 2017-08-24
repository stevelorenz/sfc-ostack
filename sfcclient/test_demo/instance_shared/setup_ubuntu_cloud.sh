#!/bin/bash
# About: Pre-configs for ubuntu-cloud

PKG_INSTALL='sudo apt install -y'
PIP_INSTALL='pip install --user'

install_pkgs() {
    echo "Install dev packages..."
    # general networking
    $PKG_INSTALL tcpdump
    $PKG_INSTALL iperf
    $PKG_INSTALL brctl
    # python dev related
    $PKG_INSTALL python
    $PKG_INSTALL python-dev
    $PKG_INSTALL python-pip
    # others
    $PKG_INSTALL tmux
}

install_ovs() {
    echo "Install OpenVswitch and kernel module..."
    $PKG_INSTALL openvswitch-switch

}

install_pip_pkgs() {
    echo "Install python packages via pip..."
    $PIP_INSTALL netifaces
}


sudo apt update
install_pkgs
sleep 3
install_ovs
sleep 3
install_pip_pkgs
