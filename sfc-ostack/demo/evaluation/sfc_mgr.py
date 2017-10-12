#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Simple manager only used for SFC evaluation tests

MARK : Really Bad codes... MUST be improved latter

Email: xianglinks@gmail.com
"""

import argparse
import sys
import time

from sfcostack import conf
from sfcostack.sfc import resource

if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description='SFC manager only used for SFC evaluation tests'
    )
    ap.add_argument('conf_file', help='Path of the sfc config file', type=str)
    ap.add_argument('init_script', help='Path of init-script for SF instances')
    ap.add_argument('operation', help='Chain operation', type=str,
                    choices=['create', 'delete'])
    ap.add_argument('sf_num', help='Number of SF instances', type=int)

    ap.add_argument('---sf_wait_time', type=float, default=10.0,
                    help='Time waiting for SFs to be ready.')

    if len(sys.argv) == 1:
        ap.print_help()
        sys.exit()
    args = ap.parse_args()

    conf_hd = conf.ConfigHolder('yaml', args.conf_file)
    auth_args = conf_hd.get_cloud_auth()
    flow_conf = conf_hd.get_sfc_flow()
    net_conf = conf_hd.get_sfc_net()

    srv_queue = []
    fc_conf = conf_hd.get_sfc_fc()

    SERVER = {
        'image': 'ubuntu-cloud',
        'flavor': 'sfc_test',
        'init_script': args.init_script,
        'ssh': {
            'user_name': 'ubuntu',
            'pub_key_name': 'sfc_test',
            'pvt_key_file': '/home/zuo/sfc_ostack_test/sfc_test.pem'
        }
    }

    opt = args.operation
    sf_num = args.sf_num
    if opt == 'c' or opt == 'create':
        print('[TEST] Create SFC with %s chain nodes' % sf_num)
        for idx in range(1, sf_num + 1):
            SERVER['name'] = 'chn%s' % idx
            srv_queue.append([SERVER.copy()])

        srv_chain = resource.ServerChain(auth_args, fc_conf['name'],
                                         fc_conf['description'],
                                         net_conf, srv_queue, True, 'pt')
        srv_chain.create(timeout=3600)

        """
        MARK: This is only a work around for tests. Just wait for all SF
        programs running properly.
        Checking status of the SF SHOULD be implmented in the resource or
        manager module.
        """
        wait_time = args.sf_wait_time * sf_num
        print('[TEST] Waiting %f seconds for SFs to be ready.' % wait_time)
        time.sleep((args.sf_wait_time * sf_num))

        port_chain = resource.PortChain(auth_args, fc_conf['name'],
                                        fc_conf['description'],
                                        srv_chain, flow_conf)
        port_chain.create()

    elif opt == 'd' or opt == 'delete':
        print('[TEST] Delete SFC with %s chain nodes' % sf_num)
        for idx in range(1, sf_num + 1):
            SERVER['name'] = 'chn%s' % idx
            srv_queue.append([SERVER.copy()])

        srv_chain = resource.ServerChain(auth_args, fc_conf['name'],
                                         fc_conf['description'],
                                         net_conf, srv_queue, True, 'pt')
        port_chain = resource.PortChain(auth_args, fc_conf['name'],
                                        fc_conf['description'],
                                        srv_chain, flow_conf)
        port_chain.delete()
        srv_chain.delete(timeout=3600)
