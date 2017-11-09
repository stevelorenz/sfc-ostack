#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Helper functions during developing

       These functions are used for temporary solutions, SHOULD be replaced with
       better implementation.

Email: xianglinks@gmail.com
"""

import os
import time

from keystoneauth1 import loading, session
from openstack import connection

from sfcostack import hot, log
from sfcostack.sfc import netsfc_clt


##############################
#  OpenStack Service Client  #
##############################

def get_service_client(service, auth_args):
    """Get proper REST-client for OpenStack service

    :param service (str): Name of the service
    :param auth_args (dict): Dict of keystone authentication arguments
    """
    # Use keystoneauth session API
    loader = loading.get_plugin_loader('password')
    auth = loader.load_from_options(**auth_args)
    sess = session.Session(auth=auth)
    if service == 'compute':
        from novaclient import client
        return client.Client(2, session=sess)
    elif service == 'networking':
        from neutronclient.v2_0 import client
        return client.Client(session=sess)
    elif service == 'orchestration':
        from heatclient import client
        return client.Client(1, session=sess)
    elif service == 'all':
        return connection.Connection(**auth_args)
    else:
        raise RuntimeError('Unknown service type!')


########################
#  Resource Operation  #
########################

def stack_create(auth_args, name, hot_str,
                 wait_complete=True, interval=3, timeout=600):
    conn = connection.Connection(**auth_args)
    heat_client = get_service_client('orchestration', auth_args)
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


#############################
#  Evaluation, demo, tests  #
#############################

def create_src_dst(sfc_conf):
    """Create source and destination hosts"""
    conn = connection.Connection(**sfc_conf.auth)
    pub_net = conn.network.find_network(sfc_conf.network.pubnet_name)
    pvt_net = conn.network.find_network(sfc_conf.network.net_name)
    pvt_subnet = conn.network.find_subnet(sfc_conf.network.subnet_name)
    sample_ins = sfc_conf.sample_server.copy()
    hot_cont = hot.HOT()
    prop = dict()
    for ins in ('src', 'dst'):
        networks = list()
        port_name = '%s_pt' % ins
        prop = {
            'name': port_name,
            'network_id': pvt_net.id,
            'fixed_ips': [{'subnet_id': pvt_subnet.id}],
        }
        networks.append(
            {'port': '{ get_resource: %s }' % port_name})
        hot_cont.resource_lst.append(
            hot.Resource(port_name, 'port', prop))

        prop = {
            'floating_network': pub_net.id,
            'port_id': '{ get_resource: %s}' % port_name
        }
        hot_cont.resource_lst.append(
            hot.Resource(ins + '_fip', 'fip', prop))

        prop = {
            'name': ins,
            'image': sample_ins['image'],
            'flavor': sample_ins['flavor'],
            'networks': networks,
            'key_name': sample_ins['ssh']['pub_key_name']
        }
        hot_cont.resource_lst.append(
            hot.Resource(ins, 'server', prop))

    stack_create(sfc_conf.auth, 'src_dst',
                 hot_cont.output_yaml_str())

    # Wait server to be ready
    for ins in ('src', 'dst'):
        srv = conn.compute.find_server(ins)
        conn.compute.wait_for_server(srv, status='ACTIVE')


def gen_lk_fwd(in_iface, out_iface,
               cidr, src_ip, dst_ip, path):
    """Generate init file for Linux kernel forwarding"""
    fmt_dict = {
        'in_iface': in_iface,
        'out_iface': out_iface,
        'cidr': cidr,
        'src_ip': src_ip,
        'dst_ip': dst_ip
    }
    init_str = """#!/bin/bash
ip link set {in_iface} up
ip link set {out_iface} up
dhclient {in_iface}
dhclient {out_iface}

ip route del {cidr} dev {in_iface}
ip route del {cidr} dev {out_iface}

# Add static routes
ip route add {src_ip} dev {in_iface}
ip route add {dst_ip} dev {out_iface}

# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward
        """.format(**fmt_dict)

    with open(path, 'w+') as f:
        f.write(init_str)
    os.chmod(path, 0o770)


def gen_py_fwd(in_iface, out_iface, br_iface,
               src_ip, dst_ip, br_ip, fake_ip,
               path):
    """Generate init file for python forwarding"""
    init_str = """#!/bin/bash
ip link set {in_iface} up
ip link set {out_iface} up

BRIDGE_IP={br_ip}
FAKE_INGRESS_IP={fake_ip}

ovs-vsctl add-br {br_iface}
ip addr add "$BRIDGE_IP/24" dev {br_iface}

ethtool --offload {br_iface} rx off tx off
ethtool --offload {in_iface} rx off tx off
ethtool --offload {out_iface} rx off tx off

BRIDGE_MAC=$(cat /sys/class/net/{br_iface}/address)

ovs-vsctl add-port {br_iface} {in_iface}
ovs-vsctl add-port {br_iface} {out_iface}

# Disable flooding to avoid looping
ovs-ofctl mod-port {br_iface} 1 no-flood
ovs-ofctl mod-port {br_iface} 2 no-flood

ovs-ofctl add-flow {br_iface} "in_port=1 actions=mod_dl_dst:$BRIDGE_MAC,mod_nw_src:$FAKE_INGRESS_IP,mod_nw_dst:$BRIDGE_IP,LOCAL"

ip route add $DST_IP dev {br_iface}
ovs-ofctl add-flow {br_iface} "in_port=local actions=mod_nw_src:$SRC_IP,mod_nw_dst:$DST_IP,output:2"

####################
#  Run SF Program  #
####################
    """.format(**{
        'in_iface': in_iface,
        'out_iface': out_iface,
        'br_iface': br_iface,
        'br_ip': br_ip,
        'fake_ip': fake_ip,
        'src_ip': src_ip,
        'dst_ip': dst_ip})

    with open(path, 'w+') as f:
        f.write(init_str)
    os.chmod(path, 0o770)
