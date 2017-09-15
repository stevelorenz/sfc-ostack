#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: SFC Resource

Email: xianglinks@gmail.com
"""

import logging
import time
from collections import OrderedDict, deque

import paramiko
from heatclient import client as heatclient
from keystoneauth1 import loading, session
from openstack import connection

from sfcostack import netsfc_clt
from sfcostack.resource import hot


class SFCRscError(Exception):
    """Base error of SFC resource"""
    pass


class ConfigInstanceError(SFCRscError):
    """Error while configuring instances"""
    pass


class SFC(object):

    """SFC Resource

    TODO:
        self.conn, sfcclient and heatclient SHOULD share the same keystone auth
        session.
    """

    def __init__(self, conf_hd):
        """Init a SFC resource"""
        self.logger = logging.getLogger(__name__)
        self.conf_hd = conf_hd
        self.sfc_stack = deque()

        auth_args = self.conf_hd.get_cloud_auth()
        self.conn = connection.Connection(**auth_args)
        self.pc_client = netsfc_clt.SFCClient(auth_args, self.logger)

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
        net_conf = self.conf_hd.get_sfc_net()
        pubnet = self.conn.network.find_network('public')
        if not pubnet:
            raise SFCRscError('Can not find the public network!')
        net = self.conn.network.find_network(net_conf['net_name'])
        if not net:
            raise SFCRscError(
                'Can not find network:%s for FC servers' % net_conf['net_name'])
        subnet = self.conn.network.find_subnet(net_conf['subnet_name'])
        if not subnet:
            raise SFCRscError(
                'Can not find the subnet:%s for FC servers.' % net_conf['subnet_name'])

        sec_grp = self.conn.network.find_security_group(
            net_conf['security_group_name'])
        if not sec_grp:
            raise SFCRscError(
                'Can not find the security group:%s for FC servers' %
                net_conf['security_group_name']
            )

        self.network_id = {
            'public': pubnet.id,
            'net': net.id,
            'subnet': subnet.id,
            'sec_grp': sec_grp.id
        }

    def _get_pp(self):
        """TODO: Get a list of to be chained port pairs
                 This CAN be used by other functions
        """
        pass

    def _get_output_hot(self):
        """Output essential resources as a HOT template

        :retype: str
        """
        fc_conf = self.conf_hd.get_sfc_fc()
        # HOT container
        hot_cont = hot.HOT(desc=fc_conf['description'])
        prop = dict()  # properties dict

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
                    'network_id': self.network_id['net'],
                    # A list of subnet IDs
                    'fixed_ips': [{'subnet_id': self.network_id['subnet']}],
                    # A list of security groups
                    'security_groups': [self.network_id['sec_grp']]
                }
                networks.append({'port': '{ get_resource: %s }' % port_name})
                hot_cont.resource_lst.append(
                    hot.Resource(port_name, 'port', prop))

            # Floating IP for remote access ports
            prop = {
                'floating_network': self.network_id['public'],
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

    def _config_server(self, srv, ip, port=22, interval=3, timeout=120):
        """Run essential configs on a FC server

        :param srv (dict): Dict of server parameters.
        :param ip (str): IP for SSH
        :param interval (float): Interval for checking SSH connection
        :param timeout (float): Timeout for connection error
        """
        net_conf = self.conf_hd.get_sfc_net()
        subnet = self.conn.network.find_subnet(net_conf['subnet_name'])
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

    def _create_flow_classifier(self):
        """Create the flow classifier

        :return: The ID of the created flow classifier
        """
        flow_conf = self.conf_hd.get_sfc_flow()

        # TODO: Use IP instead of ID
        # src_ip = flow_conf['logical_source_ip']
        # dst_ip = flow_conf['logical_destination_ip']
        # flow_conf.pop('logical_source_ip', None)
        # flow_conf.pop('logical_destination_ip', None)

        self.logger.info('Create flow classifier.')
        self.pc_client.create('flow_classifier', flow_conf)
        return self.pc_client.get_id('flow_classifier', flow_conf['name'])

    def _create_port_chain(self, fc_id):
        """Create the port chain

        :param fc_id (str): ID of the flow classifier
        """
        srv_lst = self.conf_hd.get_sfc_server()
        fc_conf = self.conf_hd.get_sfc_fc()
        pp_grp_lst = list()
        for srv in srv_lst:
            inp = srv['name'] + '_pt_in'
            outp = srv['name'] + '_pt_out'
            pp_name = '_'.join((inp, outp))
            pp_args = {
                'name': pp_name,
                'description': '',
                'ingress': self.conn.network.find_port(inp).id,
                'egress': self.conn.network.find_port(outp).id
            }
            self.pc_client.create('port_pair', pp_args)
            pp_id = self.pc_client.get_id('port_pair', pp_name)
            pp_grp_args = {
                'name': 'pp_grp_%s' % pp_name,
                'description': '',
                'port_pairs': [pp_id]
            }
            self.pc_client.create('port_pair_group', pp_grp_args)
            pp_grp_id = self.pc_client.get_id('port_pair_group',
                                              pp_grp_args['name'])
            pp_grp_lst.append(pp_grp_id)

        pc_args = {
            'name': fc_conf['name'],
            'description': 'BlaBla',
            'port_pair_groups': pp_grp_lst,
            'flow_classifiers': [fc_id]
        }
        self.pc_client.create('port_chain', pc_args)

    def create(self, timeout=300):
        """Create the service function chain

        Steps:
            - Create FC servers via HOT
            - Config FC servers via SSH
            - Create flow classifier
            - Create port chain
        """
        fc_conf = self.conf_hd.get_sfc_fc()
        hot_str = self._get_output_hot()
        self.logger.info('Create FC servers using HEAT, stacks name: %s' %
                         fc_conf['name'])
        self.heat_client.stacks.create(stack_name=fc_conf['name'],
                                       template=hot_str)

        srv_lst = self.conf_hd.get_sfc_server()

        # Wait for floating IPs have the status ACTIVE
        # for fip in self.conn.network.ips(status='DOWN'):
        #     while True:
        #         time.sleep(1)
        #         if fip.status == 'ACTIVE':
        #             break

        for srv in srv_lst:
            # MARK: the server might not be created yet
            while True:
                time.sleep(1)
                srv_ins = self.conn.compute.find_server(srv['name'])
                if srv_ins:
                    break
            # Wait for server has the status ACTIVE
            self.conn.compute.wait_for_server(srv_ins, status='ACTIVE')
            # Get the floating IP of the server
            rmt_pt = self.conn.network.find_port(srv['name'] + '_pt')
            fip = list(self.conn.network.ips(port_id=rmt_pt.id))[
                0].floating_ip_address
            try:
                self._config_server(srv, fip)
            except ConfigInstanceError as e:
                self.logger.error(e)

        self.logger.info('Create the flow classifier.')
        fc_id = self._create_flow_classifier()
        self.logger.info('Create the port chain.')
        self._create_port_chain(fc_id)

    def delete(self, timeout=300):
        """Delete the service function chain"""

        self.logger.info('Delete port chain resources.')
        for pc in self.pc_client.list('port_chain'):
            self.pc_client.delete('port_chain', pc['name'])
            time.sleep(1)
        for pp_grp in self.pc_client.list('port_pair_group'):
            self.pc_client.delete('port_pair_group', pp_grp['name'])
            time.sleep(1)
        for pp in self.pc_client.list('port_pair'):
            self.pc_client.delete('port_pair', pp['name'])
            time.sleep(1)

        self.logger.info('Delete flow classifier.')
        for fc in self.pc_client.list('flow_classifier'):
            self.pc_client.delete('flow_classifier', fc['name'])
            time.sleep(1)

        fc_conf = self.conf_hd.get_sfc_fc()
        self.logger.info('Delete FC servers using HEAT, stacks name: %s' %
                         fc_conf['name'])
        fc_stack = self.conn.orchestration.find_stack(fc_conf['name'])
        if not fc_stack:
            raise SFCRscError('Can not find stack with name: %s' %
                              fc_conf['name'])
        self.conn.orchestration.delete_stack(fc_stack)


if __name__ == "__main__":
    print('Run tests...')
