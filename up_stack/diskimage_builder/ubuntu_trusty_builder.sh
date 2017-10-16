#!/bin/bash
#
# ubuntu_trusty_builder.sh
#
# About: Build a ubuntu-cloud image with pre-installed tools via diskimage-builder

export ELEMENTS_PATH=./elements
# Build image with pre-installed packages
DIB_RELEASE=trusty disk-image-create -o ubuntu-trusty.qcow2 -p tmux,tcpdump,bridge-utils,openvswitch-switch vm ubuntu
