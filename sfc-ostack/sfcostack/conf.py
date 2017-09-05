#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Configuration Holder and Parser

Email: xianglinks@gmail.com
"""

import logging

import yaml

# Supported conf format
SUP_FMT = ('yaml', )


class ConfigError(Exception):
    """ConfigError"""
    pass


class ConfigHolder(object):

    """General container for config parameters

    Also handels parameters checking
    """

    def __init__(self, fmt, url):
        """Init a ConfigHolder object

        :param fmt (str): The format of config
        :param url (str): The URL of config
        """
        self.logger = logging.getLogger(__name__)
        self.conf_parser = ConfigParser(fmt)
        self.conf_dict = self.conf_parser.load(url)
        self._conf_logger()

    def _conf_logger(self):
        """Config logger"""
        log_conf = self.conf_dict['log']
        # default format string
        fmt_str = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        level = {
            'INFO': logging.INFO,
            'DEBUG': logging.DEBUG,
            'ERROR': logging.ERROR
        }
        logging.basicConfig(level=level[log_conf['level']],
                            # MARK: current only use console output
                            handlers=[logging.StreamHandler()],
                            format=fmt_str
                            )

    def _get_cloud_conf(self):
        """Get cloud conf"""
        if 'cloud' not in self.conf_dict:
            raise ConfigError('Missing cloud configs!')
        cloud_conf = self.conf_dict['cloud']
        for sec in ('auth', ):
            if sec not in cloud_conf:
                raise ConfigError('Missing %s configs in cloud section!' % sec)
        return cloud_conf

    def _get_sfc_conf(self):
        """Get SFC config"""
        if 'SFC' not in self.conf_dict:
            raise ConfigError('Missing SFC configs!')
        sfc_conf = self.conf_dict['SFC']
        for sec in ('flow_classifier', 'network', 'server'):
            if sec not in sfc_conf:
                raise ConfigError('Missing %s configs in SFC section!' % sec)
        return sfc_conf

    def get_cloud_auth(self):
        """Get cloud auth args"""
        auth_args = self._get_cloud_conf()['auth']
        return auth_args

    def get_sfc_flow(self):
        """Get the flow classifier"""
        flow_conf = self._get_sfc_conf()['flow_classifier']
        if len(flow_conf) > 1:
            raise ConfigError('Multiple flow classifiers are not allowed!')
        # convert to a single un-nested dict
        for key, value in flow_conf.items():
            value['name'] = key
        return value

    def get_sfc_net(self):
        """Get SFC network configs"""
        net_conf = self._get_sfc_conf()['network']
        return net_conf

    def get_sfc_server(self):
        """Get SFC servers

        :retype: list
        """
        srv_conf = self._get_sfc_conf()['server']
        srv_lst = [0] * len(srv_conf)
        for srv, conf in srv_conf.items():
            conf['name'] = srv
            srv_lst[conf['seq_num'] - 1] = conf
        return srv_lst


class ConfigParser(object):

    """Config Parser"""

    def __init__(self, fmt):
        """Init a ConfigParser"""
        self.logger = logging.getLogger(__name__)
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
        raise NotImplementedError('Not implemented yet...')
