#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
"""
About : OpenStack Networking-SFC REST Client

REST API Ref: https://docs.openstack.org/networking-sfc/latest/contributor/api.html

Note  :
    1. Only support keystone v3 identity API.
    2. This module is developed relative hurried, many improvements are needed.

Usage : Check the ./example.py

Ref   :
        1. openstack/python-keystoneclient
        2. openstack/networking-sfc

Email : xianglinks@gmail.com
"""

import logging
import time
from collections import namedtuple

from keystoneauth1 import adapter, session
from keystoneauth1.exceptions import ClientException as ks_clt_excp
from keystoneauth1.identity import v3

#############
#  Logging  #
#############


def _get_logger():
    """_get_logger"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)
    return logger


###########
#  CONST  #
###########

NEUTRON_API_VERSION = 'v2.0'


################
#  Exceptions  #
################

class SFCClientException(Exception):
    """The exception class for SFCClient"""
    pass


class RscOptTimeout(SFCClientException):
    """A resource operation is timeout"""
    pass


#################
#  REST Client  #
#################

RscPara = namedtuple('Resource_Parameter', ['url', 'name', 'plural_name'])


class SFCClient(object):
    """The REST client for OpenStack networking-sfc extension"""

    # A dict of SFC resource parameters
    rsc_dict = {
        'flow_classifier':
        RscPara('/sfc/flow_classifiers', 'flow_classifier',
                'flow_classifiers'),
        'port_pair':
        RscPara('/sfc/port_pairs', 'port_pair', 'port_pairs'),
        'port_pair_group':
        RscPara('/sfc/port_pair_groups', 'port_pair_group',
                'port_pair_groups'),
        'port_chain':
        RscPara('/sfc/port_chains', 'port_chain', 'port_chains')
    }
    rsc_tuple = tuple(rsc_dict.keys())

    def __init__(self, auth_args, logger=None):
        """Initialization of SFCClient object

        :param auth_args (dict): A dict of essential arguments for Keystone authentication
        :param logger(logging.Logger): Logger object
        """
        self.auth_args = auth_args
        if not logger:
            logger = _get_logger()
        self.logger = logger
        sess = self._construct_session()
        adap_args = {
            'user_agent': 'python-sfcclient',
            'service_type': 'network',
            'service_name': 'neutron',
            'interface': 'admin',
            # Min and maximum API version, appended at the end of the Endpoint
            'min_version': NEUTRON_API_VERSION,
            'max_version': NEUTRON_API_VERSION
        }
        # HTTP client for REST requests
        self._httpclient = adapter.Adapter(sess, **adap_args)
        # user and project IDs
        self.user_id = self._httpclient.get_user_id()
        self.project_id = self._httpclient.get_project_id()
        self.endpoint = self._httpclient.get_endpoint()

    def _construct_session(self):
        """Construct a auth-session for requests"""
        auth = v3.Password(**self.auth_args)
        return session.Session(auth)

    def _send_request(self, method, url, **kargs):
        """Send a HTTP request

        :param method (str): Request method, is converted to lowercase
        :param url: Request URL
        """
        try:
            self.logger.debug('Request URL: %s', url)
            self.logger.debug('Request Method: %s', method)
            method_to_call = getattr(self._httpclient, method.lower(), None)
            if not method_to_call:
                raise SFCClientException('Invalid request method: %s' % method)
            resp = method_to_call(url, **kargs)
        except ks_clt_excp as excp:
            self.logger.error('Error Response:')
            self.logger.error(excp.response.json())
        else:
            return resp

    # --- CRUD Operations ---

    # Each item is described as a dictionary of fields, like name, id, description etc.
    # Check REST API Ref for details

    def list(self, rsc_name):
        """List all items of a resource

        :param rsc_name (str): Name of the resource
        :retype: list
        """
        rsc_para = self.rsc_dict[rsc_name]
        resp = self._send_request('GET', rsc_para.url)
        item_lst = resp.json()[rsc_para.plural_name]
        return item_lst

    # MARK: Based on item name of a resource instead of the ID

    def find(self, rsc_name, item_name, ignore_missing=True):
        """Find a resource item with given name

        :param item_name (str): Name of a specified item of a resource with rsc_name
        :param ignore_missing (Bool): If True, None is returned if the item is not found.
                                      Otherwise, the BaseSFCClientException is raised.
        :retype: dict
        """
        for item in self.list(rsc_name):
            if item['name'] == item_name:
                return item
        if ignore_missing:
            return None
        else:
            raise SFCClientException('Can not find %s with name: %s' %
                                     (rsc_name, item_name))

    def create(self, rsc_name, item_args):
        """Create a resource item with given item arguments

        :param item_args (dict): A dict of resource item arguments
        """
        rsc_para = self.rsc_dict[rsc_name]
        item_args = {rsc_para.name: item_args}
        self._send_request('POST', rsc_para.url, json=item_args)

    def delete(self, rsc_name, item_name, ignore_missing=True):
        """Delete a created resource item with given name"""
        item = self.find(rsc_name, item_name, ignore_missing)
        if item:
            rsc_para = self.rsc_dict[rsc_name]
            self._send_request('DELETE', '/'.join((rsc_para.url, item['id'])))

    def get_id(self, rsc_name, item_name):
        """Get the ID of a resource item
        :retype: string
        """
        item = self.find(rsc_name, item_name, ignore_missing=False)
        return item['id']

    def wait(self, rsc_name, item_name, opt, interval, timeout):
        """Wait for finishing a operation for a resource item

        :param opt (str): Operation, can be 'create' or 'delete'
        :param interval (float): Number of seconds to wait between checks
        :param timeout (float): Maximum number of seconds to wait for operation
        """
        total_wait = 0
        while total_wait < timeout:
            rsc = self.find(rsc_name, item_name)
            if opt == 'create':
                if not rsc:
                    time.sleep(interval)
                    total_wait += interval
            if opt == 'delete':
                if rsc:
                    time.sleep(interval)
                    total_wait += interval
            else:
                raise RuntimeError('Unknown operation: %s' % opt)

        msg = "Timeout waiting for %s operation on %s with name: %s" % (opt, rsc_name, item_name)
        raise RscOptTimeout(msg)
