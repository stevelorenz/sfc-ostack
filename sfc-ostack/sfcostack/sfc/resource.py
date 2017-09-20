#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: SFC Resource

Email: xianglinks@gmail.com
"""

import logging
import time
from collections import deque

import paramiko
from heatclient import client as heatclient
from keystoneauth1 import loading, session
from openstack import connection

from sfcostack import hot, utils
from sfcostack.sfc import netsfc_clt

############
#  Errors  #
############


class SFCRscError(Exception):
    """Base error of SFC resource"""
    pass


class ServerChainError(SFCRscError):
    """ServerChain Error"""
    pass


class ConfigInstanceError(SFCRscError):

    """Error while configuring instances via SSH"""
    pass


class PortChainError(SFCRscError):
    """PortChain Error"""
    pass


###################
#  SFC Resources  #
###################

class ServerChain(object):

    """Server Chain

    A chain of server groups
    """

    def __init__(self, auth_args, name, desc,
                 net_conf, srv_grp_lst,
                 ssh_port=False, ssh_conf=False):
        """Init server chain object

        :param auth_args:
        :param name: Name of the server chain
        :param desc: Description
        :param net_conf: Network configs
        :param srv_grp_lst (list): A list of server groups
        :param ssh_port (Bool):
        :param ssh_conf (Bool):
        """
        self.logger = logging.getLogger(__name__)

        self.name = name
        self.desc = desc
        self.net_conf = net_conf
        self.srv_grp_lst = deque(srv_grp_lst)
        self.ssh_port = ssh_port
        # MARK: depreciated feature
        self.ssh_conf = ssh_conf

        self.conn = connection.Connection(**auth_args)
        # MARK: Since there is no examples for usage of the orchestration
        # resource in openstack-pythonsdk, the heatclient lib is used here.
        # It SHOULD be replaced with pythonsdk later
        loader = loading.get_plugin_loader('password')
        auth = loader.load_from_options(**auth_args)
        sess = session.Session(auth=auth)
        self.heat_client = heatclient.Client('1', session=sess)

        self._get_network_id()

    def _get_network_id(self):
        """Get bound network resource IDs"""
        pubnet = self.conn.network.find_network('public')
        net = self.conn.network.find_network(self.net_conf['net_name'])
        subnet = self.conn.network.find_subnet(self.net_conf['subnet_name'])
        sec_grp = self.conn.network.find_security_group(
            self.net_conf['security_group_name'])

        self.network_id = {
            'public': pubnet.id,
            'net': net.id,
            'subnet': subnet.id,
            'sec_grp': sec_grp.id
        }

    # MARK: current not used
    @utils.deprecated
    def _config_server(self, srv, ip, port=22, interval=3, timeout=120):
        """Run configs on a FC server via SSH

        :param srv (dict): Dict of server parameters.
        :param ip (str): IP for SSH
        :param interval (float): Interval for checking SSH connection
        :param timeout (float): Timeout for connection error
        """
        subnet = self.conn.network.find_subnet(self.net_conf['subnet_name'])
        ssh_conf = srv['ssh']
        ssh_clt = paramiko.SSHClient()
        # Allow connection not in the known_host
        ssh_clt.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        succ, total_time = 0, 0
        while not succ:
            try:
                succ = 1
                ssh_clt.connect(ip, port, ssh_conf['user_name'],
                                key_filename=ssh_conf['pvt_key_file'])
            except paramiko.ssh_exception.NoValidConnectionsError as error:
                succ = 0
                time.sleep(interval)
                total_time += interval
                if total_time > timeout:
                    raise ConfigInstanceError(
                        'Can not create SSH connection.' + str(error))

        self.logger.info('Config server:%s with IP:%s via SSH.'
                         % (srv['name'], ip))
        for ifce in srv['ifce']:
            for cmd in (
                'sudo ip link set %s up' % ifce,
                'sudo  %s %s' % (srv['dhcp_client'], ifce),
                # Remove duplicated routing rules
                'sudo ip route delete %s dev %s' % (subnet.cidr, ifce)
            ):
                stdin, stdout, stderr = ssh_clt.exec_command(cmd)
                # Error is detected
                if stdout.channel.recv_exit_status() != 0:
                    raise ConfigInstanceError(stderr.read())

    def get_output_hot(self):
        """Output essential resources as a HOT template

        :retype: str
        """
        hot_cont = hot.HOT()
        prop = dict()

        # MARK: CAN be better... relative straight forward
        if self.ssh_port:
            port_suffix = ('pt', 'pt_in', 'pt_out')
        else:
            port_suffix = ('pt_in', 'pt_out')

        for srv_grp in self.srv_grp_lst:
            for srv in srv_grp:
                networks = list()
                # Remote access, ingress and egress ports
                for suffix in port_suffix:
                    port_name = '_'.join((srv['name'], suffix))
                    prop = {
                        'name': port_name,
                        'network_id': self.network_id['net'],
                        # A list of subnet IDs
                        'fixed_ips': [{'subnet_id': self.network_id['subnet']}],
                        # A list of security groups
                        'security_groups': [self.network_id['sec_grp']]
                    }
                    networks.append(
                        {'port': '{ get_resource: %s }' % port_name})
                    hot_cont.resource_lst.append(
                        hot.Resource(port_name, 'port', prop))

                if self.ssh_port:
                    # Floating IP for SSH port
                    prop = {
                        'floating_network': self.network_id['public'],
                        'port_id': '{ get_resource: %s }' % (srv['name'] + '_pt')
                    }
                    hot_cont.resource_lst.append(
                        hot.Resource(srv['name'] + '_fip', 'fip', prop))

                prop = {
                    'name': srv['name'],
                    # 'key_name': srv['ssh']['pub_key_name'],
                    'image': srv['image'],
                    'flavor': srv['flavor'],
                    'networks': networks
                }
                if self.ssh_port:
                    prop.update({'key_name': srv['ssh']['pub_key_name']})

                # MARK: Use RAW bash script
                if srv['init_script']:
                    with open(srv['init_script'], 'r') as f:
                        # MARK: | is needed after user_data
                        prop.update(
                            {'user_data': '|\n' + f.read()}
                        )

                hot_cont.resource_lst.append(
                    hot.Resource(srv['name'], 'server', prop))

        return hot_cont.output_yaml_str()

    def create(self, wait_complete=True, interval=3, timeout=600):
        """Create server chain using HEAT

        :param wait_complete: Block until the stack has the status complete
        """
        hot_str = self.get_output_hot()
        self.logger.info('Create server chain using HEAT, stack name: %s' %
                         self.name)
        self.heat_client.stacks.create(stack_name=self.name,
                                       template=hot_str)

        if wait_complete:
            total_time = 0
            while total_time < timeout:
                sc_stack = self.conn.orchestration.find_stack(self.name)
                if not sc_stack:
                    continue
                elif sc_stack.status == 'CREATE_COMPLETE':
                    return
                else:
                    total_time += interval

            raise SFCRscError(
                'Creation of server chain:%s timeout!' % self.name)

    def delete(self, wait_complete=True, interval=3, timeout=600):
        self.logger.info('Delete server chain using HEAT, stacks name: %s' %
                         self.name)
        sc_stack = self.conn.orchestration.find_stack(self.name)
        if not sc_stack:
            raise SFCRscError('Can not find stack with name: %s' %
                              self.name)
        self.conn.orchestration.delete_stack(sc_stack)

        if wait_complete:
            total_time = 0
            while total_time < timeout:
                sc_stack = self.conn.orchestration.find_stack(self.name)
                if not sc_stack:
                    continue
                elif sc_stack.status == 'DELETE_COMPLETE':
                    return
                else:
                    total_time += interval

            raise SFCRscError(
                'Deletion of server chain:%s timeout!' % self.name)

    # --- ServerChain Parameters ---

    def get_srv_ppgrp_name(self):
        """Get name of port pair groups

        Format:
            [ [ (ingress_port, egress_port) ], [...] ]
        """
        pp_grp_name_lst = list()
        for srv_grp in self.srv_grp_lst:
            pp_grp = list()
            for srv in srv_grp:
                pp_grp.append(
                    (srv['name'] + '_pt_in', srv['name'] + '_pt_out'))
            pp_grp_name_lst.append(pp_grp)
        return pp_grp_name_lst

    def get_srv_ppgrp_id(self):
        """Get IDs of port pair groups

        Used by PortChain object to create port chain

        Format:
            [ [ (ingress_port_id, egress_port_id) ], [...] ]
        """
        pp_grp_id_lst = list()
        for srv_grp in self.srv_grp_lst:
            pp_grp_id = list()
            for srv in srv_grp:
                pp_id = (
                    self.conn.network.find_port(srv['name'] + '_pt_in').id,
                    self.conn.network.find_port(srv['name'] + '_pt_out').id
                )
                pp_grp_id.append(pp_id)
            pp_grp_id_lst.append(pp_grp_id)
        return pp_grp_id_lst


class PortChain(object):

    """Port Chain

    Handles flow classifier, port pair, port pair group and port chain.

    Naming Pattern:
        pp_grp_1
        pp_1_1

    TODO:
    """

    def __init__(self, auth_args, name, desc,
                 srv_chain, flow_conf):
        """Init a port chain object

        :param auth_args:
        :param name:
        :param desc:
        :param srv_chain (ServerChain):
        :param flow_conf:
        """
        self.logger = logging.getLogger(__name__)
        self.conn = connection.Connection(**auth_args)
        self.pc_client = netsfc_clt.SFCClient(auth_args, self.logger)

        self.name = name
        self.desc = desc
        self.srv_chain = srv_chain
        self.flow_conf = flow_conf

    def create(self):
        """Create port chain"""

        self.logger.info('Create flow classifier.')
        # Get logical src and dest port id
        src_pt = self.conn.network.find_port(
            self.flow_conf['logical_source_port']
        )
        dst_pt = self.conn.network.find_port(
            self.flow_conf['logical_destination_port']
        )
        self.flow_conf['logical_source_port'] = src_pt.id
        self.flow_conf['logical_destination_port'] = dst_pt.id
        self.pc_client.create('flow_classifier', self.flow_conf)
        fc_id = self.pc_client.get_id(
            'flow_classifier', self.flow_conf['name'])

        self.logger.info('Create port chain.')
        srv_ppgrp_lst = self.srv_chain.get_srv_ppgrp_id()
        pp_grp_id_lst = list()
        for grp_idx, pp_grp in enumerate(srv_ppgrp_lst):
            pp_id_lst = list()
            for pp_idx, pp in enumerate(pp_grp):
                pp_args = {
                    'name': 'pp_%s_%s' % (grp_idx, pp_idx),
                    'description': '',
                    'ingress': pp[0],
                    'egress': pp[1]
                }
                self.pc_client.create('port_pair', pp_args)
                pp_id = self.pc_client.get_id('port_pair', pp_args['name'])
                pp_id_lst.append(pp_id)
            pp_grp_args = {
                'name': 'pp_grp_%s' % grp_idx,
                'description': '',
                'port_pairs': pp_id_lst
            }
            self.pc_client.create('port_pair_group', pp_grp_args)
            pp_grp_id = self.pc_client.get_id('port_pair_group',
                                              pp_grp_args['name'])
            pp_grp_id_lst.append(pp_grp_id)

        pc_args = {
            'name': self.name,
            'description': self.desc,
            'port_pair_groups': pp_grp_id_lst,
            'flow_classifiers': [fc_id]
        }
        self.pc_client.create('port_chain', pc_args)

    def delete(self):
        """Delete the port chain"""

        self.logger.info('Delete port chain.')
        # Delete port chain
        self.pc_client.delete('port_chain', self.name)

        # Delete all port pair groups
        srv_ppgrp_lst = self.srv_chain.get_srv_ppgrp_id()
        for grp_idx in range(len(srv_ppgrp_lst)):
            pp_grp_name = 'pp_grp_%s' % grp_idx
            self.pc_client.delete('port_pair_group', pp_grp_name)

        # Delete all port pairs
        for grp_idx, pp_grp in enumerate(srv_ppgrp_lst):
            for pp_idx in range(len(pp_grp)):
                pp_name = 'pp_%s_%s' % (grp_idx, pp_idx)
                self.pc_client.delete('port_pair', pp_name)

        self.logger.info('Delete flow classifier.')
        self.pc_client.delete('flow_classifier', self.flow_conf['name'])


if __name__ == "__main__":
    print('Run tests...')
