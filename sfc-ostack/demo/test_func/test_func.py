#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About : Start demo for testing SFC functionality

Email : xianglinks@gmail.com
"""

import sys

import ipdb
from openstack import connection

from sfcostack import conf, hot, log
from sfcostack.dev import helper
from sfcostack.sfc import manager

logger = log.logger

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == '-h':
        print(
            'Usage: python3 ./test_func.py option\n'
            'Option:\n'
            '\t -src-dst: Create source and destination instance\n'
            '\t -sfc-lkf: Create SFC with kernal forwarding on all availability_zones, one SF for each zone\n'
            '\t -sfc-pyf: Create SFC with python forwarding\n'
            '\t -clean: Clean up all SFC resources\n'
        )
        sys.exit()

    print('# Read SFC config file')
    sfc_conf = conf.SFCConf()
    sfc_conf.load_file('./sfc_conf.yaml')
    log.conf_logger(level='debug')

    sample_ins = sfc_conf.server_chain[0][0].copy()

    conn = connection.Connection(**sfc_conf.auth)
    pub_net = conn.network.find_network('public')
    pvt_net = conn.network.find_network(sfc_conf.network.net_name)
    pvt_subnet = conn.network.find_subnet(sfc_conf.network.subnet_name)

    if sys.argv[1] == '-src-dst':
        print('# Create source and destination server')
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

        helper.stack_create(sfc_conf.auth, 'src-dst',
                            hot_cont.output_yaml_str())

        # Wait server to be ready
        for ins in ('src', 'dst'):
            srv = conn.compute.find_server(ins)
            conn.compute.wait_for_server(srv, status='ACTIVE')

        print('# Creat SF init file with kernel IP forwarding')
        src_ip = conn.network.find_port('src_pt').fixed_ips[0]['ip_address']
        dst_ip = conn.network.find_port('dst_pt').fixed_ips[0]['ip_address']
        subnet_cidr = pvt_subnet.cidr
        helper.gen_lk_fwd(subnet_cidr, src_ip, dst_ip,
                          sample_ins['init_script'])
        sfc_conf.flow_classifier.update(
            {
                'source_ip_prefix': '%s/32' % src_ip,
                'destination_ip_prefix': '%s/32' % dst_ip
            }
        )

    elif sys.argv[1] == '-sfc-lkf':
        print('# Launch one SF server on each availability zone')
        avail_zone_lst = conn.compute.availability_zones()
        while sfc_conf.server_chain:
            sfc_conf.server_chain.pop()
        for idx, zone in enumerate(avail_zone_lst):
            sf_ins = sample_ins.copy()
            sf_ins.pop('seq_num', None)
            sf_ins.update(
                {
                    'name': 'sf%d' % idx,
                    'availability_zone': zone.name
                }
            )
            sfc_conf.server_chain.append([sf_ins])

        mgr = manager.StaticSFCManager()
        ipdb.set_trace()
        sfc = mgr.create_sfc(sfc_conf, wait_complete=True, wait_sf=False)
        ipdb.set_trace()
        mgr.delete_sfc(sfc)

    elif sys.argv[1] == '-clean':
        helper.cleanup_port_chn(sfc_conf.auth)

    else:
        raise RuntimeError('Unknown operation!')
