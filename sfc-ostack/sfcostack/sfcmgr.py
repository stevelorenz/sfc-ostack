#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: SFC(Service Function Chain) Manager

Email: xianglinks@gmail.com
"""

import logging
import time

import paramiko
from openstack import connection

from sfcostack import sfcclient


class SFCMgrError(Exception):
    """Base error of SFCMgr"""
    pass


class SFCMgr(object):

    """SFC Resource Manager

    """

    def __init__(self, conf_hd):
        """Init a SFC Manager"""
        self.logger = logging.getLogger(__name__)
        self.conf_hd = conf_hd  # config holder

        auth_args = self.conf_hd.get_cloud_auth()
        self.conn = connection.Connection(**auth_args)
        self.sfcclient = sfcclient.SFCClient(auth_args, self.logger)

    def _get_pid(self, name):
        port = self.conn.network.find_port(name)
        return port.id

    def _create_port(self, srv):
        """Create to be chained neutron ports

        :param: srv (dict)
        :retype: tuple
        """
        pp = list()
        self.logger.info('Create ingress and egress ports for server: %s...' % srv['name'])
        net_conf = self.conf_hd.get_sfc_net()
        net = self.conn.network.find_network(net_conf['net_name'])
        base = srv['name']
        for suf in ('_in', '_out'):
            # MARK: subnet_id is not supported
            pt_args = {
                'name': base + suf,
                'network_id': net.id
            }
            self.logger.debug('Create port %s on %s'
                              % (pt_args['name'], net.name))
            self.conn.network.create_port(**pt_args)
            pp.append(pt_args['name'])
        return tuple(pp)

    def _create_server(self, srv):
        """Create to be chained servers

        :param srv (dict): a dict of server parameters.
        """
        self.logger.info('Launch SFC server %s...' % srv['name'])
        net_conf = self.conf_hd.get_sfc_net()
        # Used to associate floating IPs
        pub = self.conn.network.find_network('public')
        net = self.conn.network.find_network(net_conf['net_name'])
        sec_grp = self.conn.network.find_security_group(net_conf['security_group'])
        srv_args = {
            'name': srv['name'],
            'image_id': self.conn.compute.find_image(srv['image']).id,
            'flavor_id': self.conn.compute.find_flavor(srv['flavor']).id,
            'networks': [{"uuid": net.id}],
            'key_name': srv['ssh']['pub_key_name'],
            'security_groups': []
        }
        srv_ins = self.conn.compute.create_server(**srv_args)
        # Wait until the server is active, maximal 5 min
        srv_ins = self.conn.compute.wait_for_server(srv_ins, status='ACTIVE', wait=300)
        # Add a security group
        self.conn.compute.add_security_group_to_server(srv_ins.id, sec_grp.id)
        # Add a floating IP, the instance SHOULD only has one interface now
        ifce = list(self.conn.compute.server_interfaces(srv_ins.id))[0]
        fip_args = {
            'floating_network_id': pub.id,
            'port_id': ifce.port_id
        }
        self.logger.info('Assign a floating IP to %s' % srv['name'])
        fip = self.conn.network.create_ip(**fip_args)

        # Rename iterface to the server name
        self.conn.network.update_port(ifce.port_id,
                                      **{'name': srv['name']})

        # attach chain-interfaces to the instance
        base = srv['name']
        for suf in ('_in', '_out'):
            self.logger.info('Attach port:%s to the instance:%s'
                             % ((base + suf), srv['name']))
            pt = self.conn.network.find_port(base + suf)
            self.conn.compute.create_server_interface(srv_ins.id,
                                                      **{'port_id': pt.id})
        # config the server via SSH and floating IP
        time.sleep(1)  # slowly please...
        self._config_server(srv, fip.floating_ip_address)

    def _config_server(self, srv, ip):
        """Config the chain server via SSH

        :param srv (dict): Dict of server parameters.
        :param ip (str): IP for SSH
        """
        net_conf = self.conf_hd.get_sfc_net()
        subnet = self.conn.network.find_subnet(net_conf['subnet_name'])
        ssh_conf = srv['ssh']
        ssh_clt = paramiko.SSHClient()
        # Allow connection not in the known_host
        ssh_clt.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_clt.connect(ip, 22, ssh_conf['user_name'],
                        key_filename=ssh_conf['pvt_key_file'])
        self.logger.info('Config server:%s via SSH...' % srv['name'])
        # TODO: Replace with paras from config file
        for ifce in ['eth1', 'eth2']:
            for cmd in (
                'sudo ip link set %s up' % ifce,
                # MARK: assume dhclient is installed
                'sudo dhclient %s' % ifce,
                # Remove duplicated routing rules
                'sudo ip route delete %s dev %s' % (subnet.cidr, ifce)
            ):
                # Repeat the command if error detected
                succ = 0
                while not succ:
                    stdin, stdout, stderr = ssh_clt.exec_command(cmd)
                    succ = 1
                    if stdout.channel.recv_exit_status() != 0:
                        succ = 0
                        time.sleep(1)
        # close connection
        ssh_clt.close()

    def _create_flow_classifier(self):
        """Create the flow classifier"""
        flow_conf = self.conf_hd.get_sfc_flow()
        self.logger.info('Create the flow classifier...')
        self.sfcclient.create('flow_classifier', flow_conf)
        return self.sfcclient.get_id('flow_classifier', flow_conf['name'])

    def _create_port_chain(self, pp_lst, fc_id):
        """Create the port chain

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
            pp_grp_id = self.sfcclient.find('port_pair_group', pp_grp_args['name'])
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
            2. Launch server
            3. Create flow classifier
            4. Create port chain
        """
        srv_lst = self.conf_hd.get_sfc_server()
        pp_lst = list()
        for srv in srv_lst:
            pp_lst.append(self._create_port(srv))
            time.sleep(1)
            self._create_server(srv)
            time.sleep(1)
        fc_id = self._create_flow_classifier()
        time.sleep(1)
        self._create_port_chain(pp_lst, fc_id)
        time.sleep(1)
        self.logger.info('SFC is created.')

    def _delete_port(self):
        pass

    def _delete_server(self):
        pass

    def _delete_flow_classifier(self):
        pass

    def _delete_port_chain(self):
        pass

    def delete(self):
        # TODO
        pass

    def output(self):
        """output"""
        pass
