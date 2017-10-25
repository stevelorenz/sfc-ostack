#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Unit test for sfc-ostack.sfc.manager
"""

import os

from context import sfc
from sfc import manager


class TestSFCManager(object):

    def test_base_manager(self):
        base_mgr = manager.BaseSFCManager()
