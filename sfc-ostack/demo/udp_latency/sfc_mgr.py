#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: SFC operator only for testing
MARK : Really Bad codes... MUST be improved latter

Email: xianglinks@gmail.com
"""

import sys
import time

from sfcostack import conf
from sfcostack.sfc import resource

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Missing options!')
        sys.exit(0)

    conf_hd = conf.ConfigHolder('yaml', './sfc_conf.yaml')
    auth_args = conf_hd.get_cloud_auth()
    flow_conf = conf_hd.get_sfc_flow()
    net_conf = conf_hd.get_sfc_net()
    srv_queue = []
    fc_conf = conf_hd.get_sfc_fc()

    init_script = sys.argv[1]
    SERVER = {
        'image': 'ubuntu-cloud',
        'flavor': 'sfc_test',
        'init_script': init_script,
        'ssh': {
            'user_name': 'ubuntu',
            'pub_key_name': 'sfc_test',
            'pvt_key_file': './sfc_test.pem'
        }
    }

    opt = sys.argv[2]

    if opt == 'c' or opt == 'create':
        chn_num = int(sys.argv[3])
        print('Create SFC with %s chain nodes' % chn_num)

        for idx in range(1, chn_num + 1):
            SERVER['name'] = 'chn%s' % idx
            srv_queue.append([SERVER.copy()])

        srv_chain = resource.ServerChain(auth_args, fc_conf['name'],
                                         fc_conf['description'],
                                         net_conf, srv_queue, True, 'pt')
        srv_chain.create(timeout=3600)
        port_chain = resource.PortChain(auth_args, fc_conf['name'],
                                        fc_conf['description'],
                                        srv_chain, flow_conf)
        port_chain.create()

    elif opt == 'd' or opt == 'delete':
        chn_num = int(sys.argv[3])
        print('Delete SFC with %s chain nodes' % chn_num)

        for idx in range(1, chn_num + 1):
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
