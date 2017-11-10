#!/usr/bin/env python3
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


def test_SFCConf():
    """Test SFC conf descriptor"""
    sfc_conf = conf.SFCConf()
    sfc_conf.load_file(conf_sample_path)

    function_chain = sfc_conf.function_chain
    function_chain.availability_zone == 'nova'
    avail_hypers = function_chain.available_hypervisors
    assert avail_hypers == ['comnets-ostack-1', 'comnets-ostack-2',
                            'comnets-ostack-3']

    sample_server = sfc_conf.sample_server
    assert sample_server['image'] == 'ubuntu-cloud'
    assert sample_server['flavor'] == 'm.test'
    assert sample_server['init_script'] == './init_sf.sh'
