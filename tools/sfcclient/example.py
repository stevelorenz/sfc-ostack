#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About : Examples of using sfcclient.py

Email : xianglinks@gmail.com
"""

import sfcclient

# Arguments for authentication
AUTH_ARGS = {
    'auth_url': 'http://127.0.0.1/identity/v3',
    'project_name': 'admin',
    'user_domain_name': 'default',
    'project_domain_name': 'default',
    'username': 'admin',
    'password': 'stack',
}

sfc_clt = sfcclient.SFCClient(**AUTH_ARGS)

##########################
#  CRUD Flow Classifier  #
##########################

# For resource arguments and formats check:
# https://docs.openstack.org/networking-sfc/latest/contributor/api.html

# Arguments should be given as a dictionary
FLOW_CLSFR_ARGS = {
    'name': 'udp_port_9999',
    'description': 'All traffic to UDP port 9999',
    'ethertype': 'IPv4',
    'protocol': 'UDP',
    # MARK: for all source ports
    'source_port_range_min': 0,
    'source_port_range_max': 65535,
    'destination_port_range_min': 9999,
    'destination_port_range_max': 9999,
    'source_ip_prefix': '10.0.0.1/32',
    'destination_ip_prefix': '10.0.0.2/32',
    'logical_source_port': 'ID of the source neutron port',
    'logical_destination_port': 'ID of the destination neutron port'
}

print('# A list of all created flow classifiers:')
print(sfc_clt.list('flow_classifier'))

print('# Create a new flow classifiers with FLOW_CLSFR_ARGS')
sfc_clt.create('flow_classifier', FLOW_CLSFR_ARGS)

print('# Find a flow classifier with given name')
clsfr = sfc_clt.find('flow_classifier', 'udp_port_9999')

print('# Delete a flow classifier with given name')
sfc_clt.delete('flow_classifier', 'udp_port_9999')

#####################
#  CRUD Port Chain  #
#####################

# The Usage is as same as the flow classifier
