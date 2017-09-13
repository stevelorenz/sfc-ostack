#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: SFC Manager

Email: xianglinks@gmail.com
"""

import logging
import time
from collections import deque, OrderedDict

import paramiko
from openstack import connection

from sfcostack import hot, sfcclient


class SFCMgrError(Exception):
    """Base error of SFCMgr"""
    pass


class ConfigInstanceError(SFCMgrError):
    """Error while configuring instances"""
    pass


class SFCMgr(object):

    """SFC Manager"""

    def __init__(self, conf_hd):
        """Init a SFC Manager"""
        self.logger = logging.getLogger(__name__)
        self.conf_hd = conf_hd
        self.stack = deque()

        auth_args = self.conf_hd.get_cloud_auth()
        self.conn = connection.Connection(**auth_args)
        self.sfcclient = sfcclient.SFCClient(auth_args, self.logger)

    def _output_hot(self):
        """Output essential resources as a HOT template

        :retype: str
        """
        fc_conf = self.conf_hd.get_sfc_fc()
        # HOT container
        hot_cont = hot.HOT(desc=fc_conf['description'])

        prop = dict()  # properties dict
        # - Network, subnet
        net_conf = self.conf_hd.get_sfc_net()
        pubnet = self.conn.network.find_network('public')
        if not pubnet:
            raise SFCMgrError('Can not find the public network!')
        net = self.conn.network.find_network(net_conf['net_name'])
        if not net:
            raise SFCMgrError('Can not find network:%s for FC servers' % net_conf['net_name'])
        subnet = self.conn.network.find_subnet(net_conf['subnet_name'])
        if not subnet:
            raise SFCMgrError('Can not find the subnet:%s for FC servers.' % net_conf['subnet_name'])

        # - FC server, neutron ports, floating IPs
        srv_lst = self.conf_hd.get_sfc_server()
        # MARK: CAN be better... relative straight forward
        for srv in srv_lst:
            networks = list()
            # Remote access, ingress and egress ports
            for suffix in ('pt', 'pt_in', 'pt_out'):
                port_name = '_'.join((srv['name'], suffix))
                prop = {
                    'name': port_name,
                    'network_id': net.id,
                    # A list of subnet IDs
                    'fixed_ips': [{'subnet_id': subnet.id}]
                }
                networks.append({'port': '{ get_resource: %s }' % port_name})
                hot_cont.resource_lst.append(
                    hot.Resource(port_name, 'port', prop))

            # Floating IP for remote access ports
            prop = {
                'floating_network': pubnet.id,
                'port_id': '{ get_resource: %s }' % (srv['name'] + '_pt')
            }
            hot_cont.resource_lst.append(
                hot.Resource(srv['name'] + '_fip', 'fip', prop))

            prop = {
                'name': srv['name'],
                'key_name': srv['ssh']['pub_key_name'],
                'image': srv['image'],
                'flavor': srv['flavor'],
                'networks': networks
            }
            hot_cont.resource_lst.append(
                hot.Resource(srv['name'], 'server', prop))

        return hot_cont.output_yaml_str()

    def _config_server(self, srv, ip, port=22, interval=3, timeout=60):
        """Run essential configs on a FC server

        :param srv (dict): Dict of server parameters.
        :param ip (str): IP for SSH
        :param interval (float):
        :param timeout (float):
        """
        net_conf = self.conf_hd.get_sfc_net()
        subnet = self.conn.network.find_subnet(net_conf['subnet_name'])
        ssh_conf = srv['ssh']
        ssh_clt = paramiko.SSHClient()
        # Allow connection not in the known_host
        ssh_clt.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_clt.connect(ip, port, ssh_conf['user_name'],
                        key_filename=ssh_conf['pvt_key_file'])
        self.logger.info('Config server:%s with IP:%s via SSH...'
                         % (srv['name'], ip))
        self.logger.debug('DHCP Client: %s' % srv['dhcp_client'])
        for ifce in srv['ifce']:
            for cmd in (
                'sudo ip link set %s up' % ifce,
                'sudo  %s %s' % (srv['dhcp_client'], ifce),
                # Remove duplicated routing rules
                'sudo ip route delete %s dev %s' % (subnet.cidr, ifce)
            ):
                # Repeat the command if error detected until timeout
                total_time, succ = 0, 0
                while not succ:
                    stdin, stdout, stderr = ssh_clt.exec_command(cmd)
                    succ = 1
                    # Error is detected
                    if stdout.channel.recv_exit_status() != 0:
                        succ = 0
                        # Check wait time
                        if total_time >= timeout:
                            break
                        total_time += interval
        else:
            ssh_clt.close()

        raise ConfigInstanceError('Config server:%s timeout!' % srv['name'])

    def _create_flow_classifier(self):
        """Create the flow classifier

        :return: The ID of the created flow classifier
        """
        flow_conf = self.conf_hd.get_sfc_flow()
        self.logger.info('Create the flow classifier...')
        self.sfcclient.create('flow_classifier', flow_conf)
        return self.sfcclient.get_id('flow_classifier', flow_conf['name'])

    def _create_port_chain(self, pp_lst, fc_id):
        """TODO: Create the port chain

        :param pp_lst (list): port pair list
        """
        # 1. Create port pairs and port pair group
        pp_grp_lst = list()
        for pp in pp_lst:
            inp, outp = pp  # ingress and egress port
            pp_name = '%s_%s' % (inp, outp)
            pp_args = {
                'name': pp_name,
                'description': 'BlaBlaBla',
                'ingress': self._get_pid(inp),
                'egress': self._get_pid(outp)
            }
            self.sfcclient.create('port_pair', pp_args)
            pp_id = self.sfcclient.get_id('port_pair', pp_name)
            pp_grp_args = {
                'name': 'pp_grp_%s' % pp_name,
                'description': 'BlaBlaBla',
                'port_pairs': [pp_id]
            }
            self.sfcclient.create('port_pair_group', pp_grp_args)
            pp_grp_id = self.sfcclient.find(
                'port_pair_group', pp_grp_args['name'])
            pp_grp_lst.append(pp_grp_id)

        # 2. Create the port chain
        pc_args = {
            'name': 'test_pc',
            'description': 'BlaBlaBla',
            'port_pair_groups': pp_grp_lst,
            'flow_classifiers': [fc_id]
        }
        self.sfcclient.create('port_chain', pc_args)

    def create(self):
        """Create the service function chain

        Steps:
            1. Create neutron ports
             . Create flow classifier
             . Create port chain
        """
        hot_str = self._output_hot()
        print(hot_str)
        with open('test.yaml', 'w+') as f:
            f.write(hot_str)


if __name__ == "__main__":
    print('Run tests...')
