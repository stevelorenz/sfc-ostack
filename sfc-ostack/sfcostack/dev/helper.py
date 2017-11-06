#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Helper functions during developing

       These functions are used for temporary solutions, SHOULD be replaced with
       better implementation.

Email: xianglinks@gmail.com
"""

import time

from heatclient import client as heatclient
from keystoneauth1 import loading, session
from openstack import connection

from sfcostack import hot, log
from sfcostack.sfc import netsfc_clt

logger = log.logger


#######################
#  OpenStack Service  #
#######################

def stack_create(auth_args, name, hot_str,
                 wait_complete=True, interval=3, timeout=600):
    loader = loading.get_plugin_loader('password')
    auth = loader.load_from_options(**auth_args)
    sess = session.Session(auth=auth)
    conn = connection.Connection(**auth_args)
    heat_client = heatclient.Client('1', session=sess)
    heat_client.stacks.create(stack_name=name,
                              template=hot_str)

    if wait_complete:
        total_time = 0
        while total_time < timeout:
            sc_stack = conn.orchestration.find_stack(name)
            if not sc_stack:
                time.sleep(interval)
                total_time += interval
                continue
            elif sc_stack.status == 'CREATE_COMPLETE':
                return
            # Create in process
            else:
                time.sleep(interval)
                total_time += interval
        raise RuntimeError('Creation of stack: %s timeout!' % name)


def cleanup_port_chn(auth_args):
    """Cleanup all port chain related resources"""
    pc_client = netsfc_clt.SFCClient(auth_args)
    for pc_rsc in ('port_chain', 'flow_classifier',
                   'port_pair_group', 'port_pair'):
        for rsc in pc_client.list(pc_rsc):
            pc_client.delete(pc_rsc, rsc['name'])
            time.sleep(1)


#########################
#  For tests and demos  #
#########################

def gen_lk_fwd(cidr, src_ip, dst_ip, path):
    init_str = """#!/bin/bash
ip link set eth1 up
ip link set eth2 up
dhclient eth1
dhclient eth2

ip route del %s dev eth1
ip route del %s dev eth2

# Add static routes
ip route add %s dev eth1
ip route add %s dev eth2

# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward
        """ % (cidr, cidr, src_ip, dst_ip)

    with open(path, 'w+') as f:
        f.write(init_str)
