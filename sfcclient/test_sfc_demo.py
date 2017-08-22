#!/usr/bin/env python3
# vim:fenc=utf-8

"""
About : A simple demo for testing networking-sfc extension

Topo  : Described in ./test_topo.yaml

Email : xianglinks@gmail.com
"""

import sys

from openstack import connection

import const
import sfcclient

#################
#  Helper Func  #
#################


def get_topo_info():
    """get_topo_info"""
    info = {}
    conn = connection.Connection(**const.AUTH_ARGS)
    src_vm_port = conn.network.find_port('src_vm')
    info['src_port_id'] = src_vm_port.id
    info['src_ip'] = list(conn.network.ips(port_id=src_vm_port.id))[0].fixed_ip_address
    dst_vm_port = conn.network.find_port('dst_vm')
    info['dst_port_id'] = dst_vm_port.id
    info['dst_ip'] = list(conn.network.ips(port_id=dst_vm_port.id))[0].fixed_ip_address

    igs_port = conn.network.find_port('cp1')
    info['igs_port_id'] = igs_port.id
    egs_port = conn.network.find_port('cp2')
    info['egs_port_id'] = egs_port.id

    return info


################
#  Parameters  #
################

TP_INFO = get_topo_info()

FLOW_CLSFR_ARGS = {
    'name': 'test_fc',
    'description': 'A test flow classifier for UDP traffic',
    'ethertype': 'IPv4',
    'protocol': 'UDP',
    'source_port_range_min': 8888,
    'source_port_range_max': 8888,
    'destination_port_range_min': 9999,
    'destination_port_range_max': 9999,
    'source_ip_prefix': TP_INFO['src_ip'] + '/32',
    'destination_ip_prefix': TP_INFO['dst_ip'] + '/32',
    'logical_source_port': TP_INFO['src_port_id'],
    'logical_destination_port': TP_INFO['dst_port_id']
}


def create_flow_classifier():
    sfc_clt = sfcclient.SFCClient(const.AUTH_ARGS)
    print('# Create the flow classifier.')
    sfc_clt.create('flow_classifier', FLOW_CLSFR_ARGS)
    print(sfc_clt.list('flow_classifier'))


def delete_flow_classifier():
    sfc_clt = sfcclient.SFCClient(const.AUTH_ARGS)
    print('# Delete the flow classifier.')
    sfc_clt.delete('flow_classifier', FLOW_CLSFR_ARGS['name'])
    print(sfc_clt.list('flow_classifier'))


def create_port_chain():
    sfc_clt = sfcclient.SFCClient(const.AUTH_ARGS)

    PP_ARGS = {
        'name': 'test_pp',
        'description': 'A test port pair for chain_vm',
        'ingress': TP_INFO['igs_port_id'],
        'egress': TP_INFO['egs_port_id']
    }
    print('# Create the port pair.')
    sfc_clt.create('port_pair', PP_ARGS)
    print(sfc_clt.list('port_pair'))

    pp_id = sfc_clt.get_id('port_pair', 'test_pp')
    PP_GRP_ARGS = {
        'name': 'test_pp_grp',
        'description': 'A test port pair group for chain_vm',
        'port_pairs': [pp_id]
    }
    print('# Create the port pair group.')
    sfc_clt.create('port_pair_group', PP_GRP_ARGS)
    print(sfc_clt.list('port_pair_group'))

    pp_grp_id = sfc_clt.get_id('port_pair_group', 'test_pp_grp')
    fc_id = sfc_clt.get_id('flow_classifier', 'test_fc')
    PC_ARGS = {
        'name': 'test_pc',
        'description': 'A test port chain',
        'port_pair_groups': [pp_grp_id],
        'flow_classifiers': [fc_id]
    }
    sfc_clt.create('port_chain', PC_ARGS)
    print(sfc_clt.list('port_chain'))


def delete_port_chain():
    sfc_clt = sfcclient.SFCClient(const.AUTH_ARGS)

    print('# Delete the port pair.')
    sfc_clt.delete('port_pair', 'test_pp')
    print(sfc_clt.list('port_pair'))

    print('# Delete the port pair group.')
    sfc_clt.delete('port_pair_group', 'test_pp_grp')
    print(sfc_clt.list('port_pair_group'))

    print('# Delete the port chain.')
    sfc_clt.delete('port_chain', 'test_pc')
    print(sfc_clt.list('port_chain'))


if __name__ == "__main__":
    # build_port_chain()
    if len(sys.argv) == 1:
        raise RuntimeError('Unknown operation. Use -c for creation and -d for breaking the port chain.')
    elif sys.argv[1] == '-fc':
        print('Create the flow classifier...')
        create_flow_classifier()
    elif sys.argv[1] == '-fd':
        print('Delete the flow classifier...')
        delete_flow_classifier()
    elif sys.argv[1] == '-pc':
        print('Create the port chain...')
        create_port_chain()
    elif sys.argv[1] == '-pd':
        print('Delete the port chain...')
        delete_port_chain()
    else:
        raise RuntimeError('Unknown operation. Use -c for creation and -d for breaking the port chain.')
