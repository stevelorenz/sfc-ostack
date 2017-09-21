#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: SFC operator only for testing

Email: xianglinks@gmail.com
"""

import sys

from sfcostack import conf


SERVER = {
    'name': 'chnX',
    'image': 'ubuntu-cloud',
    'flavor': 'sfc_test',
    'init_script': './forwarding.sh',
    'ssh': {
        'user_name': 'ubuntu',
        'pub_key_name': 'sfc_test',
        'pvt_key_file': './sfc_test.pem'
    }
}


def create_sfc():
    pass


def delete_sfc():
    pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Missing options!')
        sys.exit(0)

    conf_hd = conf.ConfigHolder('yaml', './sfc_conf.yaml')
    auth_args = conf_hd.get_cloud_auth()
    flow_conf = conf_hd.get_sfc_flow()
    net_conf = conf_hd.get_sfc_net()
    srv_queue = conf_hd.get_sfc_server()
    fc_conf = conf_hd.get_sfc_fc()

    opt = sys.argv[1]

    if opt == 'c' or opt == 'create':
        chn_num = sys.argv[2]
        print('Create SFC with %s chain nodes' % chn_num)

    elif opt == 'd' or opt == 'delete':
        chn_num = sys.argv[2]
        print('Delete SFC with %s chain nodes' % chn_num)
