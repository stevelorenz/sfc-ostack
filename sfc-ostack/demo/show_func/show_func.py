#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About : Show sfc-ostack basic functionalities

Email : xianglinks@gmail.com
"""

import argparse
import sys

import ipdb
from openstack import connection

from sfcostack import conf, hot, log
from sfcostack.dev import helper
from sfcostack.sfc import manager

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Show basic functionalities of sfc-ostack.')

    parser.add_argument('conf_file', help='SFC config file(yaml).')
    parser.add_argument('alloc_method', choices=['nova_default', 'fill_one'],
                        help='Method to allocate SF servers on compute hosts')
    parser.add_argument('chain_method', choices=['default', 'min_lat'],
                        help='Method to chain SF servers')

    parser.add_argument('-n', '--number', type=int, default=1,
                        help='Number of to be created SF server(s)')

    parser.add_argument('--src_dst', action='store_true',
                        help=('Create a source and destination instance with sample_server conf. '))
    parser.add_argument('--cleanup', action='store_true',
                        help='Cleanup SFC resources')

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(0)
    args = parser.parse_args()

    sfc_conf = conf.SFCConf()
    sfc_conf.load_file(args.conf_file)
    log.conf_logger(level=sfc_conf.log.level)

    if args.cleanup:
        print('# Cleanup port chain resources')
        helper.cleanup_port_chn(sfc_conf.auth)
        sys.exit(0)

    if args.src_dst:
        print('# Create src and dst instance.')
        helper.create_src_dst(sfc_conf)
        sys.exit(0)

    sample_ins = sfc_conf.sample_server.copy()
    for idx in range(args.number):
        sample_ins['name'] = 'sf%d' % idx
        sfc_conf.server_chain.append([sample_ins.copy()])
    sfc_mgr = manager.StaticSFCManager(sfc_conf.auth)

    ipdb.set_trace()

    sfc = sfc_mgr.create_sfc(sfc_conf, args.alloc_method, args.chain_method,
                             sfc_conf.function_chain.destination_hypervisor,
                             wait_sf_ready=False)
    ipdb.set_trace()

    sfc_mgr.delete_sfc(sfc)
