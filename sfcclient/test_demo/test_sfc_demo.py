#!/usr/bin/env python3
# vim:fenc=utf-8

"""
About : A simple demo for testing networking-sfc extension

        Use a flow classifier for all UDP traffics from src_vm to dst_vm with destination port = 9999
        Simple UDP sender and receiver can be found ./instance_shared/ or iperf can be used

Topo  : Described in ./test_topo.yaml (HEAT Template)

Email : xianglinks@gmail.com
"""

import json
import sys

from openstack import connection

import conf
import sfcclient
from post_build_topo import get_topo_info

################
#  Parameters  #
################

TP_INFO = get_topo_info()

FLOW_CLSFR_ARGS = {
    'name': 'test_fc',
    'description': 'A test flow classifier for UDP traffic',
    'ethertype': 'IPv4',
    'protocol': 'UDP',
    # MARK: for all source ports
    'source_port_range_min': 0,
    'source_port_range_max': 65535,
    'destination_port_range_min': 9999,
    'destination_port_range_max': 9999,
    'source_ip_prefix': TP_INFO['src_ip'] + '/32',
    'destination_ip_prefix': TP_INFO['dst_ip'] + '/32',
    'logical_source_port': TP_INFO['src_pt_id'],
    'logical_destination_port': TP_INFO['dst_pt_id']
}


def create_flow_classifier():
    sfc_clt = sfcclient.SFCClient(conf.AUTH_ARGS)
    print('# Create the flow classifier.')
    sfc_clt.create('flow_classifier', FLOW_CLSFR_ARGS)
    print('# List of flow classifier:')
    print(sfc_clt.list('flow_classifier'))


def delete_flow_classifier():
    sfc_clt = sfcclient.SFCClient(conf.AUTH_ARGS)
    print('# Delete the flow classifier.')
    sfc_clt.delete('flow_classifier', FLOW_CLSFR_ARGS['name'])
    print('# List of flow classifier:')
    print(sfc_clt.list('flow_classifier'))


def create_pc_linear():
    """Create a linear port chain"""
    sfc_clt = sfcclient.SFCClient(conf.AUTH_ARGS)
    for chn_id in range(1, 4):
        PP_ARGS = {
            'name': 'pp_%d' % chn_id,
            'description': 'Port pair for chain_ins %d' % chn_id,
            'ingress': TP_INFO['chn%d_pt_in_id' % chn_id],
            'egress': TP_INFO['chn%d_pt_out_id' % chn_id]
        }
        print('# Create the port pair.')
        sfc_clt.create('port_pair', PP_ARGS)

        print('# Create the port pair group.')
        pp_id = sfc_clt.get_id('port_pair', 'pp_%d' % chn_id)
        PP_GRP_ARGS = {
            'name': 'pp_grp_%d' % chn_id,
            'description': 'Port pair group for chain_ins %d' % chn_id,
            'port_pairs': [pp_id]
        }
        print('# Create the port pair group.')
        sfc_clt.create('port_pair_group', PP_GRP_ARGS)

    print('# List of port pairs:')
    print(sfc_clt.list('port_pair'))
    print('# List of port pair groups:')
    print(sfc_clt.list('port_pair_group'))

    print('# Create the port chain...')
    pp_grp_lst = list()
    for chn_id in range(1, 4):
        pp_grp_lst.append(
            sfc_clt.get_id('port_pair_group', 'pp_grp_%d' % chn_id)
        )

    fc_id = sfc_clt.get_id('flow_classifier', 'test_fc')
    PC_ARGS = {
        'name': 'test_pc',
        'description': 'A test port chain',
        'port_pair_groups': pp_grp_lst,
        'flow_classifiers': [fc_id]
    }
    sfc_clt.create('port_chain', PC_ARGS)
    print(sfc_clt.list('port_chain'))


def create_port_chain():
    sfc_clt = sfcclient.SFCClient(conf.AUTH_ARGS)

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
        'port_pair_groups': pp_grp_lst,
        'flow_classifiers': [fc_id]
    }
    sfc_clt.create('port_chain', PC_ARGS)
    print('# List of port chain:')
    print(sfc_clt.list('port_chain'))


def delete_port_chain():
    sfc_clt = sfcclient.SFCClient(conf.AUTH_ARGS)

    print('# Delete all port pairs.')
    for pp in sfc_clt.list('port_pair'):
        sfc_clt.delete('port_pair', pp['name'])

    print('# Delete all port pair groups.')
    for pp_grp in sfc_clt.list('port_pair_group'):
        sfc_clt.delete('port_pair_group', pp_grp['name'])

    print('# Delete all port chains.')
    for pc in sfc_clt.list('port_chain'):
        sfc_clt.delete('port_chain', pc['name'])


if __name__ == "__main__":
    if len(sys.argv) == 1:
        raise RuntimeError('Unknown operation. Use -c for creation and -d for breaking the port chain.')
    elif sys.argv[1] == '-fc':
        print('Create the flow classifier...')
        create_flow_classifier()
    elif sys.argv[1] == '-fd':
        print('Delete the flow classifier...')
        delete_flow_classifier()
    elif sys.argv[1] == '-pcl':
        print('Create the port chain...')
        create_pc_linear()
    elif sys.argv[1] == '-pd':
        print('Delete the port chain...')
        delete_port_chain()
    else:
        raise RuntimeError('Unknown operation. Use -c for creation and -d for breaking the port chain.')
