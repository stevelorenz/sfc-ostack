#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About : Build test topology using HEAT template

Email : xianglinks@gmail.com
"""

from heatclient import client
from keystoneauth1 import loading, session
from openstack import connection

auth_args = {
    'auth_url': 'http://192.168.100.1/identity/v3',
    'project_name': 'admin',
    'user_domain_name': 'default',
    'project_domain_name': 'default',
    'username': 'admin',
    'password': 'stack',
}

conn = connection.Connection(**auth_args)

pubnet = conn.network.find_network('public')

HEAT_TPL = './test_topo.yaml'

PARAMETERS = {
    'pub_net': pubnet.id,
}


if __name__ == "__main__":
    loader = loading.get_plugin_loader('password')
    auth = loader.load_from_options(**auth_args)
    sess = session.Session(auth=auth)
    heat = client.Client('1', session=sess)
    print('Create the topology with template: %s' % HEAT_TPL)
    heat.stacks.create(stack_name='UDP_latency_measurement',
                       template=open(HEAT_TPL, 'r').read(),
                       parameters=PARAMETERS)
