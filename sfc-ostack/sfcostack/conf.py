#!/usr/bin/env python3
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
    """Config Error"""
    pass


class ConfigHolder(object):

    """Container for configuration parameters"""

    def __init__(self, fmt, url):
        """Init a ConfigHolder object

        :param fmt (str): The format of config. e.g. YAML
        :param url (str): The URL of config.
        """
        self.logger = logging.getLogger(__name__)
        self.conf_parser = ConfigParser(fmt)
        self.conf_dict = self.conf_parser.load(url)
        self._conf_logger()

    def _conf_logger(self):
        """Config shared logger"""
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
                            format=fmt_str)

    #######################
    #  Get Main Sections  #
    #######################

    def _get_cloud_conf(self):
        """Get cloud config"""
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
        for sec in ('flow_classifier', 'network', 'server_chain'):
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
            return []
        # TODO: Add support for server group
        srv_grp_lst = [0] * len(srv_conf)
        for srv, conf in srv_conf.items():
            conf['name'] = srv
            if srv_grp_lst[conf['seq_num'] - 1] != 0:
                raise ConfigError('Duplicated server sequence number')
            srv_grp_lst[conf['seq_num'] - 1] = [conf]
        return srv_grp_lst


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
        if self.fmt == 'yaml':
            with open(url, 'r') as stream:
                yaml.dump(stream)


if __name__ == "__main__":
    print('Run basic test...')
    conf_hd = ConfigHolder('yaml', './conf_example.yaml')
    print('Flow configs:')
    print(conf_hd.get_sfc_flow())
    print('SFC server configs:')
    print(conf_hd.get_sfc_server())
