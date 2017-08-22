#! /bin/sh
#
# bootstrap.sh
# Copyright (C) 2017 stack <stack@comnets-desktop>
#
# Distributed under terms of the MIT license.
#


function install_tools() {
    sudo apt update
    sudo apt install tcpdump
    sudo apt install iperf
    sudo apt install brctl
}

install_tools
