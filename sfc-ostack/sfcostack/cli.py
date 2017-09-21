#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Command-Line Tool
Email: xianglinks@gmail.com
"""

import argparse
import logging
import sys

sys.path.insert(1, '../')

from sfcostack import conf
from sfcostack.sfc import resource


def cli():
    """CLI Entry

    TODO: Add support for sub-command
    """
    logger = logging.getLogger(__name__)
    desc = 'SFC-OSTACK Framework'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument(
        'conf_path', help='Path of configuration file(YAML format).', type=str
    )
    parser.add_argument(
        'operation', help='Operation for SFC', choices=['create', 'delete']
    )

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(0)
    args = parser.parse_args()

    conf_hd = conf.ConfigHolder('yaml', args.conf_path)
    auth_args = conf_hd.get_cloud_auth()
    flow_conf = conf_hd.get_sfc_flow()
    net_conf = conf_hd.get_sfc_net()
    srv_queue = conf_hd.get_sfc_server()
    fc_conf = conf_hd.get_sfc_fc()

    if args.operation == 'create':
        logger.info('Create the SFC, config file path: %s' % args.conf_path)
        srv_chain = resource.ServerChain(auth_args, fc_conf['name'],
                                         fc_conf['description'],
                                         net_conf, srv_queue, False, 'pt_in')
        srv_chain.create()
        port_chain = resource.PortChain(auth_args, fc_conf['name'],
                                        fc_conf['description'],
                                        srv_chain, flow_conf)
        port_chain.create()

    elif args.operation == 'delete':
        logger.info('Delete the SFC, config file: %s' % args.conf_path)
        srv_chain = resource.ServerChain(auth_args, fc_conf['name'],
                                         fc_conf['description'],
                                         net_conf, srv_queue, False)
        port_chain = resource.PortChain(auth_args, fc_conf['name'],
                                        fc_conf['description'],
                                        srv_chain, flow_conf)
        port_chain.delete()
        srv_chain.delete()


def dev_test():
    """Run tests during developing"""
    conf_hd = conf.ConfigHolder('yaml', './test/conf_test.yaml')
    logger = logging.getLogger(__name__)
    logger.info('Run tests for developing...')
    auth_args = conf_hd.get_cloud_auth()
    flow_conf = conf_hd.get_sfc_flow()
    net_conf = conf_hd.get_sfc_net()
    srv_queue = conf_hd.get_sfc_server()

    # --- Test sfc.resource ---
    srv_chain = resource.ServerChain(auth_args, 'test-server-chain', 'BlaBla',
                                     net_conf, srv_queue, True)

    # srv_chain.create(True)
    srv_chain.delete(True)

    port_chain = resource.PortChain(auth_args, 'test-port-chain', 'BlaBla',
                                    srv_chain, flow_conf)
    # port_chain.create()
    # port_chain.delete()


if __name__ == "__main__":
    # dev_test()
    cli()
