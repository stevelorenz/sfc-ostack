#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
"""
About : Build the topology for testing

Email : xianglinks@gmail.com
"""

from heatclient import client
from keystoneauth1 import loading, session
from openstack import connection

from const import AUTH_ARGS


def _get_public_net():
    """Get the ID of the public network"""
    conn = connection.Connection(**AUTH_ARGS)
    pub = conn.network.find_network('public')
    if not pub:
        raise RuntimeError('Can not find the public network')
    return pub.id


# Path of the HOT template
HEAT_TPL = './test_topo.yaml'

# Template input parameters
PARAMETERS = {
    'public_net': _get_public_net(),
    # Name of image for instances
    'image_name': 'ubuntu-cloud',
    # 'image_name': 'cirros-0.3.4-x86_64-uec',
    # Name of flavor
    'flavor_name': 'm1.small'
}


if __name__ == "__main__":
    loader = loading.get_plugin_loader('password')
    auth = loader.load_from_options(**AUTH_ARGS)
    sess = session.Session(auth=auth)
    heat = client.Client('1', session=sess)
    print('Create the topology with template: %s' % HEAT_TPL)
    heat.stacks.create(stack_name='sfc-test',
                       template=open(HEAT_TPL, 'r').read(),
                       parameters=PARAMETERS
                       )
