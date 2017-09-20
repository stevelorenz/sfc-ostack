#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: The SFC-Ostack Resource Manager

Managed Resources:

    - OpenStack Resources: nova, neutron
    - SFC Resources: port pair, port pair group, port chain

Email: xianglinks@gmail.com
"""

import json
import logging
import os
import sys
# MARK: For tests in the ifmain section
sys.path.insert(0, '../')
import time
from collections import deque

from openstack import connection

from sfcostack import sfcclient


PICKLE_PATH = os.path.join(
    os.getenv('HOME'),
    '.sfc_ostack/rsc/')


class RscMgrError(Exception):
    """RscMgrError"""
    pass


class RscOptError(RscMgrError):
    """General Resource Operation Error"""
    pass


class RscOptTimeout(RscOptError):
    """Resource operation timeout error"""
    pass


class RscMgr(object):

    """SFC-Ostack Resource Manager

    - Manage Mechanism
    - Resource Format
    """

    def __init__(self, auth_args, safe_mode=False):
        """Init a resource manager

        :param auth_args (dict): Cloud authentication arguments
        :param safe_mode (Bool)
        """
        self.logger = logging.getLogger(__name__)
        self.safe_mode = safe_mode
        # Resource stack
        self.rsc_stack = deque()
        # Cloud connection
        self.conn = connection.Connection(**auth_args)

        # Dispatch tables of resource operation functions
        # MARK: This maybe not elegant, any better solutions, please email me.
        self.rsc_create_func = {
            'network': self.conn.network.create_network,
            'subnet': self.conn.network.create_subnet,
            'server': self.conn.compute.create_server
        }

        self.rsc_delete_func = {
            'network': self.conn.network.delete_network,
            'subnet': self.conn.network.delete_subnet,
            'server': self.conn.compute.delete_server
        }

        self.rsc_seek_func = {
            'network': self.conn.network.find_network,
            'subnet': self.conn.network.find_subnet,
            'server': self.conn.compute.find_server
        }

    ################
    #  Stack CRUD  #
    ################

    def push(self, rsc):
        """Inserts an object at the top of the resource stack.

        :param rsc (tuple):
        """
        self.rsc_stack.append(rsc)

    def pop(self):
        return self.rsc_stack.pop()

    def clear(self):
        """Remove all resources in the stack"""
        self.rsc_stack.clear()

    def peek(self):
        """Returns the resource at the top of the stack without removing it."""
        pass

    ########################
    #  Resource Operation  #
    ########################

    def _wait_rsc_created(self, rsc, interval, timeout):
        """Wait for a resource to be created

        :param rsc (tuple): Resource tuple
        :param interval (float):
        :param timeout (float):
        """
        rsc_type, rsc_args = rsc
        seek_func = self.rsc_seek_func.get(rsc_type, None)
        total_wait = 0
        while total_wait < timeout:
            # resource object
            rsc_obj = seek_func(rsc_args['name'])
            if rsc_obj:
                # Found
                return None
            # Not found
            total_wait += interval
            self.logger.debug('%s Wait additional %s seconds',
                              rsc_args['name'], total_wait)
        raise RscOptTimeout('Creation of %s:%s timeout!' %
                            (rsc_type, rsc_args['name']))

    def _wait_rsc_deleted(self, rsc, interval, timeout):
        """Wait for a resource to be deleted"""
        rsc_type, rsc_args = rsc
        seek_func = self.rsc_seek_func.get(rsc_type, None)
        total_wait = 0
        while total_wait < timeout:
            # resource object
            rsc_obj = seek_func(rsc_args['name'])
            if not rsc_obj:
                # Not found
                return None
            # Found
            total_wait += interval
            self.logger.debug('%s Wait additional %s seconds',
                              rsc_args['name'], total_wait)
        raise RscOptTimeout('Delete of %s:%s timeout!' %
                            (rsc_type, rsc_args['name']))

    def rsc_create(self):
        """Create all resources in the stack

        Order: First pushed, first created
        """
        queue = self.rsc_stack.copy()
        while queue:
            rsc = queue.popleft()  # pop the first element
            rsc_type, rsc_args = rsc
            # Get create function from the dispatch table
            func = self.rsc_create_func.get(rsc_type, None)
            # Check resource type
            if not func:
                raise RscOptError('Unknown resource type: %s' % rsc_type)
            rsc_obj = func(**rsc_args)  # create resource

            # General checking
            if self.safe_mode:
                self._wait_rsc_created(rsc, 2, 120)

            # Special actions for special resources
            if rsc_type == 'server':
                self.conn.compute.wait_for_server(rsc_obj, status='ACTIVE', failures=[
                                                  'ERROR'], interval=2, wait=300)

    def rsc_delete(self):
        """Delete all resources in the stack

        Order: Last pushed, first deleted
        """
        stack = self.rsc_stack.copy()
        while stack:
            rsc = stack.pop()
            print(rsc)

    ########################
    #  Serialization Data  #
    ########################

    def load(self, path):
        """load

        :param path (str):
        """
        pass

    def dump(self, path):
        """dump

        :param path (str):
        """
        rsc_stack = list(self.rsc_stack)
        # default override
        with open(path, 'w+') as pick_file:
            json.dump(rsc_stack, pick_file)

    def dumps(self):
        """dumps"""
        rsc_stack = list(self.rsc_stack)
        return json.dumps(rsc_stack)


if __name__ == "__main__":
    print('Run basic tests for rscmgr.py...')
    # Arguments for authentication
    AUTH_ARGS = {
        'auth_url': 'http://192.168.100.1/identity/v3',
        'project_name': 'admin',
        'user_domain_name': 'default',
        'project_domain_name': 'default',
        'username': 'admin',
        'password': 'stack',
    }
    test_conn = connection.Connection(**AUTH_ARGS)
    rsc_mgr = RscMgr(AUTH_ARGS, safe_mode=True)
    print(rsc_mgr.dumps())
    # 1. Create net and subnet
    net_args = {
        'name': 'net1'
    }
    rsc_mgr.push(('network', net_args))
    rsc_mgr.rsc_create()
    rsc_mgr.clear()  # remove all resources
    print(rsc_mgr.dumps())
    subnet_args = {
        'name': 'subnet1',
        'cidr': '10.0.0.0/24',
        'gateway_ip': '10.0.0.1',
        'network_id': test_conn.network.find_network('net1').id,
        'ip_version': 4
    }
    rsc_mgr.push(('subnet', subnet_args))
    print(rsc_mgr.dumps())
    rsc_mgr.rsc_create()
    rsc_mgr.clear()

    # 2. Launch multiple instances
    for suf in ('1', '2', '3'):
        srv_args = {
            'name': 'test-server' + suf,
            'image_id': test_conn.compute.find_image('ubuntu-cloud').id,
            'flavor_id': test_conn.compute.find_flavor('m1.small').id,
            'networks': [{"uuid": test_conn.network.find_network('net1').id}],
            'security_groups': []
        }
        rsc_mgr.push(('server', srv_args))
    print(rsc_mgr.dumps())
    rsc_mgr.dump('./blabla.json')
    rsc_mgr.rsc_create()
