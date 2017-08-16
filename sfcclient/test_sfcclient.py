#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About : Unittest for OpenStack Networking-SFC REST Client

Topo  :
    src_vm --- chain_vm -- dst_vm

Dep   : 1.sfcclient
        2.python-openstacksdk

Email : xianglinks@gmail.com
"""
import unittest

from openstack import connection

import sfcclient

##################
#  Pub Variable  #
##################

AUTH_ARGS = {
    'auth_url': 'http://192.168.0.194/identity/v3',
    'project_name': 'admin',
    # MARK: domains must be added for keystone v3
    'user_domain_name': 'default',
    'project_domain_name': 'default',
    'username': 'admin',
    'password': 'stack',
}


################
#  Util Funcs  #
################

def dict2str(dict_obj):
    """Convert a dict to a printable string"""
    dic_str = '\n'.join('{}:{}'.format(key, val) for key, val in dict_obj.items())
    return dic_str


def stack_clean_up(auth_args):
    """General cleanups for OpenStack resources

    :param auth_args(dict)
    """
    conn = connection.Connection(**auth_args)
    proj = conn.identity.find_project(auth_args['project_name'])

    print('[INS] Delete all instances...')
    for server in conn.compute.servers():
        conn.compute.delete_server(server.id)

    # TODO
    # MARK: The router interfaces should be firstly removed properly
    # print('[NET] Delete all routers...')

    print('[NET] Delete all networks...')
    for net in conn.network.networks(project_id=proj.id):
        # skip the public network
        if net.name == 'public':
            continue
        # delete all ports
        for port in conn.network.ports(network_id=net.id):
            conn.network.delete_port(port, ignore_missing=True)
        # delete all subnets
        for subnet in net.subnet_ids:
            conn.network.delete_subnet(subnet, ignore_missing=True)
        conn.network.delete_network(net, ignore_missing=True)

    print('[SECGRP] Delete all security groups...')
    for sec_gp in conn.network.security_groups(project_id=proj.id):
        if sec_gp.name == 'default':
            continue
        conn.network.delete_security_group(sec_gp)

    print('[KEYPAIR] Delete all SSH keypairs...')
    for keypair in conn.compute.keypairs():
        conn.compute.delete_keypair(keypair)

    print('Cleanup finishes.')


def create_test_topo():
    """Create a topo for testing sfcclients

    :return: A dict of useful topo parameters, used in sfcclient tests.
    """
    print('# Creating a topo for tests...')
    # key params of the topo in a dict
    topo_params = dict()

    conn = connection.Connection(**AUTH_ARGS)
    proj = conn.identity.find_project(AUTH_ARGS['project_name'])
    print('[SECGRP] Create a test security group...')
    sec_gp = conn.network.create_security_group(
        name='test', project_id=proj.id,
        description='Only for testing, allow all ICMP, TCP and UDP ingress access'
    )
    # Add rules
    print('[SECGRP] Add rules, allow ICMP, TCP and UDP ingress for all addresses...')
    for ptl in ('icmp', 'tcp', 'udp'):
        conn.network.create_security_group_rule(
            security_group_id=sec_gp.id,
            direction='ingress',
            # allow all ip addresses
            remote_ip_prefix='0.0.0.0/0',
            protocol=ptl,
            port_range_max=None,
            port_range_min=None,
            ethertype='IPv4')

    print('[KEYPAIR] Create a default SSH keypair...')
    print("Create Key Pair: %s" % 'default')
    dft_keypair = conn.compute.create_keypair(name='default')

    print('[NET] Create network topology...')
    print('[NET] Create network net1...')
    net1 = conn.network.create_network(name='net1')
    print('[NET] Create sub-network subnet1...')
    subnet_1 = conn.network.create_subnet(
        name='subnet1',
        network_id=net1.id,
        ip_version='4',
        cidr='10.0.0.0/24',
        is_dhcp_enabled=True,
        dns_nameservers=['141.30.1.1'],
        gateway_ip='10.0.0.1')

    print('[NET] Create to be chained ports...')
    for i in range(1, 3):
        conn.network.create_port(
            name='p%d' % i,
            network_id=net1.id,
            # MARK: disable port security feature
            is_port_security_enabled=False
        )

    print('[INS] Launch instances...')
    img = conn.compute.find_image('cirros-0.3.4-x86_64-uec')
    flavor = conn.compute.find_flavor('m1.tiny')
    sec_gp = conn.network.find_security_group('test')
    net = conn.network.find_network('net1')

    for srv_name in ('src_vm', 'dst_vm', 'chain_vm'):
        print('[INS] Launch %s' % srv_name)
        srv = conn.compute.create_server(
            name=srv_name, image_id=img.id, flavor_id=flavor.id, key_name='default',
            networks=[{'uuid': net.id}], security_groups=[]
        )
        # wait for instance to be active
        srv = conn.compute.wait_for_server(srv)
        # add the test security group
        conn.compute.add_security_group_to_server(srv.id, sec_gp.id)
        # get the iface ID and IP
        srv_iface = next(conn.compute.server_interfaces(srv.id), None)
        if not srv_iface:
            raise RuntimeError('Can not get the interface of the %s' % srv_name)
        srv_iface_param = {
            'port_id': srv_iface.port_id,
            'fix_ip': srv_iface.fixed_ips[0]['ip_address']
        }
        if srv_name == 'chain_vm':
            # attach addtional ports
            p1 = conn.network.find_port('p1')
            p2 = conn.network.find_port('p2')
            if not p1 or not p2:
                raise RuntimeError('p1, p2 does not exist...')
            print('[INS] Attach p1 and p2 to %s...' % srv_name)
            conn.compute.create_server_interface(srv.id,
                                                 **{'port_id': p1.id})
            conn.compute.create_server_interface(srv.id,
                                                 **{'port_id': p2.id})
            srv_iface_param.update({'ingress_port': p1.id,
                                    'egress_port': p2.id})

        topo_params['%s' % srv_name] = srv_iface_param
    return topo_params

########################################################################################################################
#                                                        Tests                                                         #
########################################################################################################################


def test_flow_classifier():
    stack_clean_up(AUTH_ARGS)
    topo_params = create_test_topo()
    print('# Running tests for flow classifier opts...')
    flowclsfr_client = sfcclient.FlowClassifierClient(AUTH_ARGS)

    print('## List all flow classifiers')
    print(flowclsfr_client.list())

    print('## Create a new flow classifier: FC_Test')
    flowclsfr_args = {
        'name': 'FC_Test',
        'description': 'Test UDP Flow Classifier',
        # 'ethertype': ethertype,
        'protocol': 'UDP',
        'source_ip_prefix': '%s/32' % topo_params['src_vm']['fix_ip'],
        'destination_ip_prefix': '%s/32' % topo_params['dst_vm']['fix_ip'],
        'source_port_range_min': 8888,
        'source_port_range_max': 8888,
        'destination_port_range_min': 9999,
        'destination_port_range_max': 9999,
        'logical_source_port': topo_params['src_vm']['port_id'],
        'logical_destination_port': topo_params['dst_vm']['port_id'],
    }
    print('To be used FC_Test Parameters: ')
    print(dict2str(flowclsfr_args))
    flowclsfr_client.create(flowclsfr_args)
    print('## List all flow classifiers')
    print(flowclsfr_client.list())

    print('## Find the flow classifier FC_Test')
    clsfr = flowclsfr_client.find('FC_Test')
    print('Found FC_Test Parameters: ')
    print(dict2str(clsfr))

    print('## Delete the flow classifier FC_Test')
    flowclsfr_client.delete('FC_Test')
    print('## List all flow classifiers')
    print(flowclsfr_client.list())

    print('\n#Finish tests for FlowClassifierClient')


def test_port_chain():
    print('# Running tests for port pair opts...')
    stack_clean_up(AUTH_ARGS)
    topo_params = create_test_topo()
    pc_client = sfcclient.PortChainClient(AUTH_ARGS)
    print('## List all port pairs')
    pc_client.list_pp()
    pp_args = {
        'name': 'Test_PP',
        'description': 'A port pair for testing',
        'ingress': topo_params['chain_vm']['ingress_port'],
        'egress': topo_params['chain_vm']['egress_port']
    }
    print('## Create a new port pair')
    pc_client.create_pp(pp_args)
    print('## List all port pairs')
    print(pc_client.list_pp())

    print('## Find the port pair Test_PP')
    pp = pc_client.find_pp('Test_PP')
    print('Found PP Parameters: ')
    print(dict2str(pp))

    print('## Delete the port pair Test_PP')
    pc_client.delete_pp('Test_PP')
    print('## List all port pairs')
    print(pc_client.list_pp())


if __name__ == '__main__':
    print('# Running tests for sfcclient module...\n')
    test_flow_classifier()
    # test_port_chain()
