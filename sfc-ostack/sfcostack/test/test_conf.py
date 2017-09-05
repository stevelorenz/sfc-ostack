#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
"""
About : Test config
        Arguments are stored in a dict

Email : xianglinks@gmail.com
"""

import os

##################
#  Cloud Config  #
##################

# Arguments for authentication
AUTH_ARGS = {
    'auth_url': 'http://192.168.100.1/identity/v3',
    'project_name': 'admin',
    'user_domain_name': 'default',
    'project_domain_name': 'default',
    'username': 'admin',
    'password': 'stack',
}

SSH_KEY_ARGS = {
    'name': 'test',
    'path': './test.pem'
}

SEC_GRP_ARGS = {
    'name': 'test'
}

IMAGE_ARGS = {
    'name': 'ubuntu-cloud',
    # Path of the image
    'path': os.getenv('HOME') + '/ostack_image/ubuntu-trusty-customized.qcow2',
    'disk_format': 'qcow2',
    'container_format': 'bare',
    'visibility': 'public',
}

HEAT_ARGS = {
    'stack_name': 'sfc-ostack-test',
    'format': 'HOT',
    'tpl_path': './test_topo.yaml'
}

####################
#  Network Config  #
####################

NET_ARGS = {
    'pvt_net_name': 'net1',
    'pvt_subnet_name': 'subnet1',
    'pvt_subnet_cidr': '10.0.0.0/24',
    'pvt_subnet_gw': '10.0.0.1',
    'pvt_subnet_dns': '141.30.1.1'
}

#####################
#  Instance Config  #
#####################

INS_ARGS = {
    # --- Flavor ---
    'flavor': {
        'name': 'm.test',
        'vcpus': '1',
        # in GB, for ubuntu-cloud minimal 1.8G
        'disk': '2',
        # in MB
        'ram': '1024'
    }
}
