#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
"""
About : Build test topology using HEAT template

Email : xianglinks@gmail.com
"""

from heatclient import client
from keystoneauth1 import loading, session
from openstack import connection

import test_conf as conf


def _get_public_net():
    """Get the ID of the public network"""
    conn = connection.Connection(**conf.AUTH_ARGS)
    pub = conn.network.find_network('public')
    if not pub:
        raise RuntimeError('Can not find the public network')
    return pub.id


# Path of the heat template
HEAT_TPL = conf.HEAT_ARGS['tpl_path']

# Template input parameters
PARAMETERS = {
    'pub_net': _get_public_net(),
    'image_name': conf.IMAGE_ARGS['name'],
    'pvt_net_name': conf.NET_ARGS['pvt_net_name'],
    'pvt_subnet_name': conf.NET_ARGS['pvt_subnet_name'],
    'pvt_subnet_cidr': conf.NET_ARGS['pvt_subnet_cidr'],
    'pvt_subnet_gw': conf.NET_ARGS['pvt_subnet_gw'],
    'pvt_subnet_dns': conf.NET_ARGS['pvt_subnet_dns'],
    'key_name': conf.SSH_KEY_ARGS['name'],
    'flavor_name': conf.INS_ARGS['flavor']['name']
}


if __name__ == "__main__":
    loader = loading.get_plugin_loader('password')
    auth = loader.load_from_options(**conf.AUTH_ARGS)
    sess = session.Session(auth=auth)
    heat = client.Client('1', session=sess)
    print('Create the topology with template: %s' % HEAT_TPL)
    heat.stacks.create(stack_name=conf.HEAT_ARGS['stack_name'],
                       template=open(HEAT_TPL, 'r').read(),
                       parameters=PARAMETERS
                       )
