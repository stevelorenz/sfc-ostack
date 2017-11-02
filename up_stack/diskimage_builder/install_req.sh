#!/bin/bash
# MARK: Create a virtualenv before running the script
#       $ virtualenv -p /usr/bin/python2 venv
#       $ source ./venv/bin/activate

echo "Install requirements..."
pip install diskimage-builder
sudo apt-get install qemu-utils
