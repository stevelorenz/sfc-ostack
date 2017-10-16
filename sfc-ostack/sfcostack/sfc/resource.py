#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: SFC Resource

MARK(Zuo, 12.10.2017):
    Currently all CRUD operations are implemented in the resource classes, which
    is simple but not architecturally bas. This SHOULD be separated.

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
from sfcostack.log import logger
# MARK: CAN be replaced with openstack-neutronclient with v2 API
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


class PortChainError(SFCRscError):
    """PortChain Error"""
    pass


###################
#  SFC Resources  #
###################

"""
MARK(Zuo, 12-10.2017):

The reason of separation of ServerChain and PortChain is trying to reduce the
overhead for in future implemented dynamic chain topology updating. The creation
of the ServerChain takes much time, which SHOULD be avoided if the SFs on the
server remain unchanged.
"""


class ServerChain(object):

    """Server Chain, a chain of server groups.

    Each server group SHOULD contains a list of server instances with the same
    type of SFs, which matches the definition of a port pair group(mainly used
    for traffic balancing).
    """

    def __init__(self, auth_args, name, desc,
                 net_conf, srv_grp_lst, sep_access_port=False,
                 fip_port=None):
        """Init server chain object

        :param auth_args (dict):
        :param name (str): Name of the server chain
        :param desc (str): Description of the server chain, optional
        :param net_conf (dict): Network configs
        :param srv_grp_lst (list): A list of server groups
        :param sep_access_port (Bool): If True, a separate port is created for
                                       remote access
        :param fip_port (str): Indicate which port to bind the floating IP
                               pt: sep_access_port
                               pt_in: ingress port
                               pt_out: egress port
        """

        self.name = name
        self.desc = desc
        self.net_conf = net_conf
        self.srv_grp_lst = deque(srv_grp_lst)
        self.sep_access_port = sep_access_port
        self.fip_port = fip_port

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
        # TODO: Add support for security group

        self.network_id = {
            'public': pubnet.id,
            'net': net.id,
            'subnet': subnet.id
        }

    def _get_ins_fips(self):
        """Get a list of floating IPs of all server instances

        :retype: list
        """
        fip_lst = list()
        for srv_grp in self.srv_grp_lst:
            grp_fip_lst = list()
            for srv in srv_grp:
                fip_pt_name = srv['name'] + '_%s' % self.fip_port
                fip = list(
                    self.conn.network.ips(port_id=fip_pt_name.id))[0].floating_ip_address
                grp_fip_lst.append(fip)
            fip_lst.append(grp_fip_lst)
        return fip_lst

    def _get_ssh_clients(self):
        """TODO: Get a list of SSH clients for server instances"""
        pass

    def get_output_hot(self):
        """Output essential resources as a HOT template

        :retype: str
        """
        hot_cont = hot.HOT()
        prop = dict()

        # MARK: CAN be better... relative straight forward
        if self.sep_access_port:
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
                        # TODO: Add support for security group
                        # 'security_groups': [self.network_id['sec_grp']]
                    }
                    networks.append(
                        {'port': '{ get_resource: %s }' % port_name})
                    hot_cont.resource_lst.append(
                        hot.Resource(port_name, 'port', prop))

                if self.fip_port:
                    prop = {
                        'floating_network': self.network_id['public'],
                    }
                    if self.fip_port == 'pt':
                        prop['port_id'] = '{ get_resource: %s }' % (
                            srv['name'] + '_pt')
                    elif self.fip_port == 'pt_in':
                        prop['port_id'] = '{ get_resource: %s }' % (
                            srv['name'] + '_pt_in')
                    elif self.fip_port == 'pt_out':
                        prop['port_id'] = '{ get_resource: %s }' % (
                            srv['name'] + '_pt_out')
                    else:
                        raise ServerChainError('Invalid floating IP port!')

                    hot_cont.resource_lst.append(
                        hot.Resource(srv['name'] + '_fip', 'fip', prop))

                prop = {
                    'name': srv['name'],
                    'image': srv['image'],
                    'flavor': srv['flavor'],
                    'networks': networks
                }

                if srv.get('ssh', None):
                    prop['key_name'] = srv['ssh']['pub_key_name']

                # MARK: Only test RAW bash script
                if srv.get('init_script', None):
                    logger.debug('Read the init bash script: %s'
                                 % srv['init_script'])
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

        :param wait_complete (Bool): Block until the stack has the status complete
        """
        hot_str = self.get_output_hot()
        logger.info('Create the server chain using HEAT, stack name: %s' %
                    self.name)
        self.heat_client.stacks.create(stack_name=self.name,
                                       template=hot_str)
        if timeout:
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
        logger.info('Delete the server chain using HEAT, stacks name: %s' %
                    self.name)
        sc_stack = self.conn.orchestration.find_stack(self.name)
        if not sc_stack:
            raise SFCRscError('Can not find stack with name: %s' %
                              self.name)
        self.conn.orchestration.delete_stack(sc_stack)

        if timeout:
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

        :retype: list
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

        :retype: list
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

    # --- Service Function related Methods ----
    # Used to check if the SF runs properly on the server instances

    def wait_proc(self, proc_pattern, max_retry=3):
        """Wait until a specific process is running on all server instances

        Use SSH and pgrep to check the proc_pattern, default option: -f, MAY be
        replaced with a better method

        :param proc_pattern (str): Pattern for pgrep checking
        """
        check_cmd = "pgrep -f '%s'" % proc_pattern
        fip_lst = self._get_ins_fips()
        ssh_clt = paramiko.SSHClient()
        ssh_clt.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        for srv_grp, fip_grp in zip(self.srv_grp_lst, fip_lst):
            for srv, fip in zip(srv_grp, fip_grp):
                retry = 0
                while retry <= max_retry:
                    try:
                        ssh_clt.connect(fip, 22, srv['ssh']['user_name'],
                                        key_filename=srv['ssh']['pvt_key_file'])
                    except Exception:
                        logger.warn(
                            '[FIP:%s] Can not connect to instance, try again after 3 seconds'
                            % fip
                        )
                        time.sleep(3)
                        retry += 1
                    else:
                        break
                else:
                    ssh_clt.close()
                    raise ServerChainError(
                        '[FIP:%s] Can not connect to instance via SSH' % fip)

                trans = ssh_clt.get_transport()
                retry = 0
                while retry <= max_retry:
                    channel = trans.open_session()
                    channel.exec_command(check_cmd)
                    status = channel.recv_exit_status()
                    if status == 0:
                        break
                    else:
                        logger.warn(
                            '[FIP:%s] Process is not running, recheck after 10 seconds.'
                            % fip
                        )
                        time.sleep(10)
                        retry += 1
                else:
                    ssh_clt.close()
                    raise ServerChainError(
                        '[FIP:%s] SF Process is not running' % fip)

                ssh_clt.close()


class PortChain(object):

    """Port Chain

    Handles flow classifier, port pair, port pair group and port chain.

    Resource Dependency:

        Port Pair: neutron ingress and egress ports
        Port Pair Group: port pairs
        Port Chain: port pairs, port pair groups and flow classifier

    CRUD Operation:

        - Creation:
            In order to reduce the latency of packets(the time difference between
            last SFC-modified packet and the first SFC-modified packet), the flow
            classifier is created after finishing creation of all port pairs and
            port pair groups. The port chain is created finally, which depends on
            flow classifier.

        - Deletion:
            Similar to the creation, the flow classifier will be deleted after
            finishing deleting the port chain.


    Naming Pattern:

        Port Pair: pp_(port pair group index)_(port pair index) e.g. pp_1_1
        Port Pair Group: pp_grp_(port pair group index) e.g. pp_grp_1
        Port Chain: Get name from user config
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
        logger = logging.getLogger(__name__)
        self.conn = connection.Connection(**auth_args)
        self.pc_client = netsfc_clt.SFCClient(auth_args, logger)

        self.name = name
        self.desc = desc
        self.srv_chain = srv_chain
        self.flow_conf = flow_conf

    def create(self):
        """Create port chain"""
        logger.info('Create port pairs and port pair groups.')
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

        # Get logical src and dest port id
        src_pt = self.conn.network.find_port(
            self.flow_conf['logical_source_port']
        )
        dst_pt = self.conn.network.find_port(
            self.flow_conf['logical_destination_port']
        )
        self.flow_conf['logical_source_port'] = src_pt.id
        self.flow_conf['logical_destination_port'] = dst_pt.id
        logger.info('Create the flow classifier.')
        self.pc_client.create('flow_classifier', self.flow_conf)
        fc_id = self.pc_client.get_id(
            'flow_classifier', self.flow_conf['name'])

        pc_args = {
            'name': self.name,
            'description': self.desc,
            'port_pair_groups': pp_grp_id_lst,
            'flow_classifiers': [fc_id]
        }
        logger.info('Create the port chain: %s.' % self.name)
        self.pc_client.create('port_chain', pc_args)

    def delete(self):
        """Delete the port chain"""
        logger.info('Delete the port chain: %s' % self.name)
        # Delete port chain
        self.pc_client.delete('port_chain', self.name)

        logger.info('Delete the flow classifier.')
        self.pc_client.delete('flow_classifier', self.flow_conf['name'])

        # Delete all port pair groups
        logger.info('Delete port pair groups and port pairs.')
        srv_ppgrp_lst = self.srv_chain.get_srv_ppgrp_id()
        for grp_idx in range(len(srv_ppgrp_lst)):
            pp_grp_name = 'pp_grp_%s' % grp_idx
            self.pc_client.delete('port_pair_group', pp_grp_name)

        # Delete all port pairs
        for grp_idx, pp_grp in enumerate(srv_ppgrp_lst):
            for pp_idx in range(len(pp_grp)):
                pp_name = 'pp_%s_%s' % (grp_idx, pp_idx)
                self.pc_client.delete('port_pair', pp_name)


# TODO: Add Mininet net liked SFC resource object
# MARK: Dynamic management of the SFC SHOULD implemented in ./manager.py
class SFC(object):
    pass
