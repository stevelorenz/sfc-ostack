#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About : OpenStack Networking-SFC REST Client

REST API Ref: https://docs.openstack.org/networking-sfc/latest/contributor/api.html

Note  : 1. Only support keystone v3 identity API
        2. This module is developed relative hurried, many improvements are needed.

Ref   : openstack/python-congressclient
        openstack/python-keystoneclient

Email : xianglinks@gmail.com
"""

import logging

from keystoneauth1 import adapter, session
from keystoneauth1.exceptions import ClientException as ks_client_excp
from keystoneauth1.identity import v3

#############
#  Logging  #
#############

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
dft_fmt = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
stream_handler.setFormatter(dft_fmt)
logger.addHandler(stream_handler)

###########
#  CONST  #
###########

NEUTRON_API_VERSION = 'v2.0'


################
#  Exceptions  #
################

class BaseSFCClientException(Exception):
    """The base exception class for SFCClient"""
    pass


#################
#  REST Client  #
#################

class BaseSFCClient(object):

    """Base REST client for OpenStack networking-sfc Extension"""

    def __init__(self, auth_args):
        """Initialization of Client object.

        :param auth_args (dict): A dict of authentication arguments.
        """
        self.auth_args = auth_args
        sess = self._construct_session()
        # MARK: A session should be provided for the adapter
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
        """Construct a session for requests"""
        auth = v3.Password(**self.auth_args)
        return session.Session(auth)

    def _send_request(self, method, url, **kargs):
        """Send a HTTP request

        :param method (str): Request method, is converted to lowercase
        :param url: Request URL
        """
        try:
            logger.debug('Request URL: %s', url)
            logger.debug('Request Method: %s', method)
            method_to_call = getattr(self._httpclient, method.lower(), None)
            if not method_to_call:
                raise BaseSFCClientException(
                    'Invalid request method: %s' % method)
            resp = method_to_call(url, **kargs)
        except ks_client_excp as excp:
            logger.error('Error Response:')
            logger.error(excp.response.json())
        else:
            return resp

    # --- CRUD Operations ---

    def _list(self, rsc_url):
        """Get a list of all items of a given resource URL

        :param rsc_url (str): Resource URL
        """
        resp = self._send_request('GET', rsc_url)
        item_lst = resp.json()[rsc_url.split('/')[-1]]
        return item_lst

    def _find(self, rsc_url, rsc_name, item_name, ignore_missing):
        """Find a resource item with a given item name

        :param rsc_url (str): URL of the resource
        :param rsc_name (str): Name of the resource
        :param item_name (str): Name of the item
        :param ignore_missing (Bool): If True, None is returned if the item is not found.
                                      Otherwise, the BaseSFCClientException is raised.
        """
        # MARK: search can be optimized
        for item in self._list(rsc_url):
            if item['name'] == item_name:
                return item
        if ignore_missing:
            return None
        else:
            raise BaseSFCClientException('Can not find %s with name: %s'
                                         % (rsc_name, item_name))

    def _create(self, rsc_url, rsc_name, item_args):
        """Create a resource item with given item arguments

        :param item_args (dict): A dict of resource item arguments
        """
        item_args = {rsc_name: item_args}
        self._send_request('POST', rsc_url, json=item_args)

    def _update(self, rsc_url, rsc_name, item_name, item_args, ignore_missing):
        """Update a created resource item"""
        item = self._find(rsc_url, rsc_name, item_name, ignore_missing)
        if item:
            item_args = {rsc_name: item_args}
            self._send_request('PUT',
                               '/'.join((rsc_url, item['id'])),
                               json=item_args)

    def _delete(self, rsc_url, rsc_name, item_name, ignore_missing):
        """Delete a created resource item"""
        item = self._find(rsc_url, rsc_name, item_name, ignore_missing)
        if item:
            self._send_request('DELETE',
                               '/'.join((rsc_url, item['id'])))


class FlowClassifierClient(BaseSFCClient):

    """Client for flow classifier APIs"""

    rsc_url = '/sfc/flow_classifiers'
    rsc_name = 'flow_classifier'

    def __init__(self, auth_args):
        super(FlowClassifierClient, self).__init__(auth_args)

    def list(self):
        return self._list(self.rsc_url)

    def find(self, item_name, ignore_missing=False):
        return self._find(self.rsc_url, self.rsc_name,
                          item_name, ignore_missing)

    def create(self, item_args):
        self._create(self.rsc_url, self.rsc_name, item_args)

    def update(self, item_name, item_args, ignore_missing=False):
        self._update(self.rsc_url, self.rsc_name, item_name,
                     item_args, ignore_missing)

    def delete(self, item_name, ignore_missing=False):
        self._delete(self.rsc_url, self.rsc_name, item_name, ignore_missing)


class PortChainClient(BaseSFCClient):

    """Client for port chain APIs"""

    pp_rsc_url = '/sfc/port_pairs'
    pp_rsc_name = 'port_pair'

    ppgrp_rsc_url = '/sfc/port_pair_groups'
    ppgrp_rsc_name = 'port_pair_group'

    pc_rsc_url = '/sfc/port_chains'
    pc_rsc_name = 'port_chain'

    # --- Port Pair ---

    def __init__(self, auth_args):
        super(PortChainClient, self).__init__(auth_args)

    def list_pp(self):
        self._list(self.pp_rsc_url)

    def find_pp(self, item_name, ignore_missing=False):
        self._find(self.pp_rsc_url, self.pp_rsc_name,
                   item_name, ignore_missing)

    def create_pp(self, item_args):
        self._create(self.pp_rsc_url, self.pp_rsc_name, item_args)

    def update_pp(self, item_name, item_args, ignore_missing=False):
        self._update(self.pp_rsc_url, self.pp_rsc_name, item_name,
                     item_args, ignore_missing)

    def delete_pp(self, item_name, ignore_missing):
        self._delete(self.pp_rsc_url, self.pp_rsc_name,
                     item_name, ignore_missing)

    # --- Port Pair Groups ---

    def list_ppgrp(self):
        self._list(self.ppgrp_rsc_url)

    def find_ppgrp(self, item_name, ignore_missing=False):
        self._find(self.ppgrp_rsc_url, self.ppgrp_rsc_name,
                   item_name, ignore_missing)

    def create_ppgrp(self, item_args):
        self._create(self.ppgrp_rsc_url, self.ppgrp_rsc_name, item_args)

    def update_ppgrp(self, item_name, item_args, ignore_missing=False):
        self._update(self.ppgrp_rsc_url, self.ppgrp_rsc_name, item_name,
                     item_args, ignore_missing)

    def delete_ppgrp(self, item_name, ignore_missing):
        self._delete(self.ppgrp_rsc_url, self.ppgrp_rsc_name,
                     item_name, ignore_missing)

    # --- Port Chain ---

    def list_pc(self):
        self._list(self.pc_rsc_url)

    def find_pc(self, item_name, ignore_missing=False):
        self._find(self.pc_rsc_url, self.pc_rsc_name,
                   item_name, ignore_missing)

    def create_pc(self, item_args):
        self._create(self.pc_rsc_url, self.pc_rsc_name, item_args)

    def update_pc(self, item_name, item_args, ignore_missing=False):
        self._update(self.pc_rsc_url, self.pc_rsc_name, item_name,
                     item_args, ignore_missing)

    def delete_pc(self, item_name, ignore_missing):
        self._delete(self.pc_rsc_url, self.pc_rsc_name,
                     item_name, ignore_missing)


if __name__ == "__main__":
    HELP_INFO = 'Use this module with import'
    print(HELP_INFO)
