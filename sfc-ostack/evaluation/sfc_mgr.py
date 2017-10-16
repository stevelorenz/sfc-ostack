#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Simple manager ONLY used for SFC evaluation tests

Email: xianglinks@gmail.com
"""

import argparse
import sys
import time

from sfcostack import conf
from sfcostack.sfc import resource

# Shared server base conf for evaluation
EVA_SERVER = {
    'image': 'ubuntu-cloud',
    'flavor': 'sfc_test',
    'ssh': {
        'user_name': 'ubuntu',
        'pub_key_name': 'sfc_test',
        'pvt_key_file': '/home/zuo/sfc_ostack_test/sfc_test.pem'
    }
}


class EvaSFCMgr(object):

    """SFC Manager for evaluation"""

    def __init__(self, conf_file, init_script):
        conf_hd = conf.ConfigHolder('yaml', conf_file)
        self.auth_args = conf_hd.get_cloud_auth()
        self.flow_conf = conf_hd.get_sfc_flow()
        self.net_conf = conf_hd.get_sfc_net()
        self.fc_conf = conf_hd.get_sfc_fc()
        self.server = EVA_SERVER.copy()
        self.server['init_script'] = init_script

    def create_sc(self, sf_num, sep_port=True,
                  fip_port='pt', sf_wait_time=None, timeout=3600):
        print('[TEST] Create ServerChain with %d SFs' % sf_num)
        srv_queue = list()
        for idx in range(1, sf_num + 1):
            self.server['name'] = 'chn%s' % idx
            srv_queue.append([self.server.copy()])
        srv_chain = resource.ServerChain(self.auth_args,
                                         self.fc_conf['name'],
                                         self.fc_conf['description'],
                                         self.net_conf, srv_queue, sep_port,
                                         fip_port)
        srv_chain.create(timeout=timeout)

        if sf_wait_time:
            wait_time = sf_wait_time * sf_num
            print('[TEST] Waiting %f seconds for SFs to be ready.' % wait_time)
            time.sleep(wait_time)

        return srv_chain

    def delete_sc(self, srv_chain, timeout=3600):
        print('[TEST] Delete ServerChain: %s' % srv_chain.name)
        srv_chain.delete(timeout=timeout)

    def create_pc(self, srv_chain):
        print('[TEST] Create the PortChain with SC: %s' % srv_chain.name)
        port_chain = resource.PortChain(self.auth_args,
                                        self.fc_conf['name'],
                                        self.fc_conf['description'],
                                        srv_chain, self.flow_conf)
        port_chain.create()
        return port_chain

    def delete_pc(self, port_chain):
        print('[TEST] Delete the PortChain: %s' % port_chain.name)
        port_chain.delete()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description='SFC manager only used for SFC evaluation tests'
    )
    ap.add_argument('conf_file', help='Path of the sfc config file', type=str)
    ap.add_argument('init_script', help='Path of init-script for SF instances')
    ap.add_argument('operation', help='SFC operation', type=str,
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
    EVA_SERVER['init_script'] = args.init_script

    srv_queue = []
    fc_conf = conf_hd.get_sfc_fc()

    opt = args.operation
    sf_num = args.sf_num
    if opt == 'c' or opt == 'create':
        print('[TEST] Create SFC with %s chain nodes' % sf_num)
        for idx in range(1, sf_num + 1):
            EVA_SERVER['name'] = 'chn%s' % idx
            srv_queue.append([EVA_SERVER.copy()])

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
            EVA_SERVER['name'] = 'chn%s' % idx
            srv_queue.append([EVA_SERVER.copy()])

        srv_chain = resource.ServerChain(auth_args, fc_conf['name'],
                                         fc_conf['description'],
                                         net_conf, srv_queue, True, 'pt')
        port_chain = resource.PortChain(auth_args, fc_conf['name'],
                                        fc_conf['description'],
                                        srv_chain, flow_conf)
        port_chain.delete()
        srv_chain.delete(timeout=3600)
