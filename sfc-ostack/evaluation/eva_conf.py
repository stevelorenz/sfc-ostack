#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Shared configuration for SFC evaluation tests
       Used by ./eva_helper.py to generate scripts

Email: xianglinks@gmail.com
"""

auth_args = {
    'auth_url': 'http://127.0.0.1/identity/v3',
    'project_name': 'admin',
    'user_domain_name': 'default',
    'project_domain_name': 'default',
    'username': 'admin',
    'password': 'password',
}

img_args = {
    'name': 'ubuntu-cloud',
    'path': '/opt/stack/sfcostack/ubuntu-trusty.qcow2',
    'disk_format': 'qcow2',
    'container_format': 'bare',
    'visibility': 'public',
}

flavor_args = {
    'name': 'sfc_test',
    'vcpus': '1',
    # in GB, for ubuntu-cloud minimal 1.8G
    'disk': '2',
    'ram': '1024'  # in MB
}
