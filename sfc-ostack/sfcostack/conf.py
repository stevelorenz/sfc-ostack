#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: SFC configuration holder

Email: xianglinks@gmail.com
"""

import logging

import yaml
from addict import Dict as ADict

from sfcostack import log, utils

logger = log.logger

# Supported conf format
SUP_FMT = ('yaml', )


class ConfigError(Exception):
    """Config error"""
    pass


# TODO: To be removed
# ------------------------------------------------------------------------------
@utils.deprecated
class ConfigHolder(object):

    """Container for configuration parameters"""

    def __init__(self, fmt, url):
        """Init a ConfigHolder object

        :param fmt (str): The format of config. e.g. YAML
        :param url (str): The URL of config.
        """
        self.conf_parser = ConfigParser(fmt)
        self.conf_dict = self.conf_parser.load(url)
        self._conf_logger()

    def _conf_logger(self):
        """Config shared logger"""
        log_conf = self.conf_dict['log']
        log.conf_logger(level=log_conf['level'].lower())

    #######################
    #  Get Main Sections  #
    #######################

    def _get_cloud_conf(self):
        """Get cloud config"""
        if 'cloud' not in self.conf_dict:
            raise ConfigError('Missing cloud configs!')
        _cloud_conf = self.conf_dict['cloud']
        for sec in ('auth', ):
            if sec not in _cloud_conf:
                raise ConfigError('Missing %s configs in cloud section!' % sec)
        return _cloud_conf

    def _get_sfc_conf(self):
        """Get SFC config"""
        if 'SFC' not in self.conf_dict:
            raise ConfigError('Missing SFC configs!')
        sfc_conf = self.conf_dict['SFC']
        for sec in ('function_chain', 'flow_classifier', 'network',
                    'server_chain'):
            if sec not in sfc_conf:
                raise ConfigError('Missing %s configs in SFC section!' % sec)
        return sfc_conf

    ####################
    #  Public Methods  #
    ####################

    def get_cloud_auth(self):
        """Get cloud auth args"""
        return self._get_cloud_conf()['auth']

    def get_sfc_fc(self):
        """Get function chain args"""
        return self._get_sfc_conf()['function_chain']

    def get_sfc_flow(self):
        """Get flow classifier args"""
        flow_conf = self._get_sfc_conf()['flow_classifier']
        return flow_conf

    def get_sfc_net(self):
        """Get SFC network args"""
        return self._get_sfc_conf()['network']

    def get_sfc_server(self):
        """Get server chain

        :retype: list
        """
        srv_conf = self._get_sfc_conf()['server_chain']
        if not srv_conf:
            logger.warning('No SF server(s) described in the conf file.')
            return []
        # TODO: Add support for server group
        srv_grp_lst = [0] * len(srv_conf)
        for srv, conf in srv_conf.items():
            conf['name'] = srv
            if srv_grp_lst[conf['seq_num'] - 1] != 0:
                raise ConfigError('Duplicated server sequence number.')
            srv_grp_lst[conf['seq_num'] - 1] = [conf]
            return srv_grp_lst


class ConfigParser(object):

    """Config Parser"""

    def __init__(self, fmt):
        """Init a ConfigParser"""
        if fmt == 'yaml':
            self.fmt = 'yaml'
        else:
            raise ConfigError('Unsupported config format!')

    def load(self, url):
        """Load config from a URL

        :param url (str)
        :return: A nested dict of all configs
        :retype: dict
        """
        # MARK: Current only implement the file input
        if self.fmt == 'yaml':
            with open(url, 'r') as stream:
                conf_dict = yaml.safe_load(stream)
        return conf_dict

    def dump(self, url):
        """Dump config to a URL"""
        if self.fmt == 'yaml':
            with open(url, 'r') as stream:
                yaml.dump(stream)

# ------------------------------------------------------------------------------


class SFCConf(object):

    """Ostack-SFC configuration descriptor

    Properties use addict whose values are both gettable and settable using attributes
    """

    def __init__(self, conf_dict=None):
        """Init a conf descriptor"""

        self._cloud_conf = None
        self._sfc_conf = None
        self._log_conf = None

        # Config properties
        self._auth = None
        self._function_chain = None
        self._flow_classifier = None
        self._network = None
        self._server_chain = None
        self._sample_server = None

        self._conf_dict = conf_dict
        if self._conf_dict:
            self._construct_sfc_conf()

    @staticmethod
    def _check_sec_arg(sec, conf, arg_lst):
        error_info = 'Missing {} configs in {} section!'
        for arg in arg_lst:
            if arg not in conf:
                raise ConfigError(error_info.format(arg, sec))

    def _construct_sfc_conf(self):
        """Construct a addict formatted SFC conf from nested dict"""
        for sec in ('log', 'cloud', 'SFC'):
            if sec not in self._conf_dict:
                raise ConfigError('Missing %s base section!' % sec)
        self._log_conf = ADict(self._conf_dict['log'])
        self._cloud_conf = ADict(self._conf_dict['cloud'])
        self._sfc_conf = ADict(self._conf_dict['SFC'])

        self._set_cloud_auth(self._cloud_conf.auth)
        self._set_sfc_function_chain(self._sfc_conf.function_chain)
        self._set_sfc_flow_classifier(self._sfc_conf.flow_classifier)
        self._set_sfc_network(self._sfc_conf.network)
        self._set_sfc_server_chain(self._sfc_conf.server_chain)
        self._set_sample_server(self._sfc_conf.sample_server)

    def load_file(self, path, fmt='yaml'):
        """Load SFC configs from file

        :param path (str): Path of config file
        :param fmt (str): File format, support yaml
        """
        if fmt == 'yaml':
            with open(path, 'r') as conf_file:
                self._conf_dict = yaml.safe_load(conf_file)
        else:
            raise ConfigError('Unknown conf file format!')
        self._construct_sfc_conf()

    def dump_file(self, path, fmt='yaml'):
        """Dump SFC configs into file"""
        if fmt == 'yaml':
            with open(path, 'w+') as conf_file:
                conf_file.write(yaml.safe_dump(self._conf_dict))
        else:
            raise ConfigError('Unknown conf file format!')

    ######################
    #  Property Setters  #
    ######################

    def _get_log(self):
        return self._log_conf

    def _set_log(self, log_conf):
        self._check_sec_arg('log', log_conf,
                            ('level', ))
        self._log_conf = ADict(log_conf)

    def _get_cloud_auth(self):
        return self._auth

    def _set_cloud_auth(self, auth_conf):
        self._check_sec_arg('cloud, auth', auth_conf,
                            ('auth_url', 'project_name', 'project_domain_name',
                             'username', 'user_domain_name', 'password')
                            )
        self._auth = ADict(auth_conf)

    def _get_sfc_funtion_chain(self):
        return self._function_chain

    def _set_sfc_function_chain(self, chn_conf):
        self._check_sec_arg('SFC, function_chain', chn_conf,
                            ('name', 'description', 'destination_hypervisor')
                            )
        self._function_chain = ADict(chn_conf)

    def _get_sfc_flow_classifier(self):
        return self._flow_classifier

    def _set_sfc_flow_classifier(self, flow_conf):
        self._check_sec_arg('SFC, flow_classifier', flow_conf,
                            ('name', 'description', 'ethertype', 'protocol',
                             'source_port_range_min', 'source_port_range_max',
                             'destination_port_range_min',
                             'destination_port_range_max',
                             'source_ip_prefix',
                             'destination_ip_prefix',
                             'logical_source_port',
                             'logical_destination_port')
                            )
        self._flow_classifier = ADict(flow_conf)

    def _get_sfc_network(self):
        return self._network

    def _set_sfc_network(self, net_conf):
        self._check_sec_arg('SFC, network', net_conf,
                            ('pubnet_name', 'net_name', 'subnet_name')
                            )
        self._network = ADict(net_conf)

    def _get_sfc_server_chain(self):
        return self._server_chain

    def _set_sfc_server_chain(self, srv_chn_conf):
        if not srv_chn_conf:
            # logger.warning('No SF server in server_chain conf!')
            self._server_chain = []
            return
        # MARK: Duplicated sequence number is not allowed
        # TODO: Add support for server group
        srv_chn = [0] * len(srv_chn_conf)
        for srv, conf in srv_chn_conf.items():
            conf['name'] = srv
            if srv_chn[conf['seq_num'] - 1] != 0:
                raise ConfigError('Duplicated server sequence number.')
            self._check_sec_arg('SFC, server_chain, %s' % srv,
                                conf,
                                ('image', 'flavor', 'init_script')
                                )
            srv_chn[conf['seq_num'] - 1] = [conf]
        self._server_chain = srv_chn

    def _get_sample_server(self):
        return self._sample_server

    def _set_sample_server(self, sample_server):
        self._check_sec_arg('sample server', sample_server,
                            ('image', 'flavor', 'init_script')
                            )
        self._sample_server = ADict(sample_server)

    log = property(fget=_get_log, fset=_set_log)
    auth = property(fget=_get_cloud_auth, fset=_set_cloud_auth)
    function_chain = property(fget=_get_sfc_funtion_chain,
                              fset=_set_sfc_function_chain)
    flow_classifier = property(fget=_get_sfc_flow_classifier,
                               fset=_set_sfc_flow_classifier)
    network = property(fget=_get_sfc_network,
                       fset=_set_sfc_network)
    server_chain = property(fget=_get_sfc_server_chain,
                            fset=_set_sfc_server_chain)
    sample_server = property(fget=_get_sample_server,
                             fset=_set_sample_server)
