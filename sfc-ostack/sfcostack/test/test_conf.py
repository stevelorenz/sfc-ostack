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

sfc_conf = conf.SFCConf()
sfc_conf.load_file(conf_sample_path)
