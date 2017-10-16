#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Unit test for sfc-ostack.conf
"""

import os

from context import conf

conf_sample_path = os.path.join(
    os.path.dirname(__file__),
    '../../share/sfcostack_tpl_sample.yaml'
)

#################
#  Conf Parser  #
#################

#################
#  Conf Holder  #
#################

conf_hd = conf.ConfigHolder('yaml', conf_sample_path)


def test_conf_holder():
    auth_args = {
        'auth_url': 'http://192.168.0.1/identity/v3',
        'project_name': 'admin',
        'user_domain_name': 'default',
        'project_domain_name': 'default',
        'username': 'admin',
        'password': 'stack',
    }
    assert conf_hd.get_cloud_auth() == auth_args
