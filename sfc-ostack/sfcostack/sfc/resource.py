#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: SFC Resource

Email: xianglinks@gmail.com
"""

import time
from collections import deque

import paramiko
from heatclient import client as heatclient
from keystoneauth1 import loading, session
from openstack import connection

from sfcostack import hot, log, utils
# MARK: CAN be replaced with openstack-neutronclient with v2 API
from sfcostack.sfc import netsfc_clt

logger = log.logger


############
#  Errors  #
############

class SFCRscError(Exception):
    """Base error of SFC resource"""
    pass


class SFCDespError(SFCRscError):
    """SFC Descriptor error"""
    pass


class ServerChainError(SFCRscError):
    """ServerChain error"""
    pass


class PortChainError(SFCRscError):
    """PortChain error"""
    pass


class SFCError(SFCRscError):
    """SFC error"""
    pass


###################
#  SFC Resources  #
###################

class SFCDesp(object):
    """TODO: SFC Descriptor(Config), used by manager to CRUD SFC

    SHOULD contain config about:
        - SFC classifier configs
        - SFC networking configs
        - SF instance ordering, dependency and init config
    """
    pass


"""
MARK(Zuo, 12-10.2017):

The reason of separation of ServerChain and PortChain is trying to reduce the
overhead for in future implemented dynamic chain topology updating. The creation
of the ServerChain takes much time, which SHOULD be avoided if the SFs on the
server remain unchanged.
"""

# TODO: Add get and set methods for server groups instead of playing with nested
# lists


class ServerChain(object):

    """Server chain, a chain of server groups.

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

    #  --- HEAT helper func ---

    def _wait_creation_complete(self, stack_name, status='CREATE_COMPLETE',
                                timeout=300, interval=3):
        total_time = 0
        while total_time < timeout:
            stack = self.conn.orchestration.find_stack(stack_name)
            # Not created in the db
            if not stack:
                time.sleep(interval)
                total_time += interval
                continue
            elif stack.status == status:
                return
            # Create in process
            else:
                logger.debug(
                    'Stack: %s creation is in progress.' % stack_name
                )
                time.sleep(interval)
                total_time += interval
        raise ServerChainError(
            'Stack: %s creation timeout!' % stack_name)

    def _wait_deletion_complete(self, stack_name, timeout=300, interval=3):
        total_time = 0
        while total_time < timeout:
            stack = self.conn.orchestration.find_stack(stack_name)
            # Delete in progress
            if stack:
                time.sleep(interval)
                total_time += interval
            else:
                return
        raise ServerChainError(
            'Stack: %s deletion timeout!' % stack_name)

    # --- Get server chain info ---

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

    def get_srv_num(self):
        """Get number of all servers in the chain"""
        srv_num = 0
        for srv_grp in self.srv_grp_lst:
            srv_num += len(srv_grp)
        return srv_num

    def get_srv_fips(self, no_grp=False):
        """Get a list of floating IPs of all server instances

        Used by SFC manager for SF checking and remote access

        :retype: list
        """
        fip_lst = list()
        for srv_grp in self.srv_grp_lst:
            grp_fip_lst = list()
            for srv in srv_grp:
                fip_pt = self.conn.network.find_port(
                    srv['name'] + '_%s' % self.fip_port
                )
                fip = list(
                    self.conn.network.ips(port_id=fip_pt.id))[0].floating_ip_address
                grp_fip_lst.append(fip)
            fip_lst.append(grp_fip_lst)

        if no_grp:
            n_fip_lst = list()
            for fip_grp in fip_lst:
                n_fip_lst.extend(fip_grp)
            return n_fip_lst

        return fip_lst

    def get_srv_ssh_tuple(self, no_grp=False):
        """Get a list of SSH tuples for all server instances

        SSH Tuple: (fip, username, pvt_key)
        """
        ssh_tuple_lst = list()
        for srv_grp in self.srv_grp_lst:
            grp_ssh_tuple_lst = list()
            for srv in srv_grp:
                srv_ssh = srv['ssh']
                fip_pt = self.conn.network.find_port(
                    srv['name'] + '_%s' % self.fip_port
                )
                fip = list(
                    self.conn.network.ips(port_id=fip_pt.id))[0].floating_ip_address
                grp_ssh_tuple_lst.append(
                    (fip, srv_ssh['user_name'], srv_ssh['pvt_key_file'])
                )

            ssh_tuple_lst.append(grp_ssh_tuple_lst)

        if no_grp:
            n_ssh_tuple_lst = list()
            for grp_ssh_tuple_lst in ssh_tuple_lst:
                n_ssh_tuple_lst.extend(grp_ssh_tuple_lst)
            return n_ssh_tuple_lst

        return ssh_tuple_lst

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

    # --- CR of server chain ---

    def get_output_hot(self, only_network=False):
        """Output essential resources as a HOT template

        :param only_network (Bool): If True, only add networking resources
        """
        hot_cont = hot.HOT()
        prop = dict()

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

                if only_network:
                    return hot_cont.output_yaml_str()

                prop = {
                    'name': srv['name'],
                    'image': srv['image'],
                    'flavor': srv['flavor'],
                    'networks': networks
                }

                if srv.get('ssh', None):
                    prop['key_name'] = srv['ssh']['pub_key_name']

                if srv.get('availability_zone', None):
                    prop['availability_zone'] = srv['availability_zone']
                    logger.debug('%s, availability zone: %s'
                                 % (srv['name'], srv['availability_zone']))

                # MARK: Only test RAW bash script
                if srv.get('init_script', None):
                    logger.debug('%s, read init bash script, path: %s'
                                 % (srv['name'], srv['init_script']))
                    with open(srv['init_script'], 'r') as init_file:
                        # MARK: | is needed after user_data
                        prop.update(
                            {'user_data': '|\n' + init_file.read()}
                        )

                hot_cont.resource_lst.append(
                    hot.Resource(srv['name'], 'server', prop))

        return hot_cont.output_yaml_str()

    def create_network(self):
        """Create networking resources"""

        logger.debug(
            'Create networking resources for server chain: %s, stack name: %s',
            self.name, self.name
        )
        hot_tpl = self.get_output_hot(only_network=True)
        self.heat_client.stacks.create(stack_name=self.name,
                                       template=hot_tpl)
        self._wait_creation_complete(self.name)

    # MARK: Use HEAT updating function
    def create_instance(self, wait_complete=True):
        """Create all instances in the server chain"""
        hot_tpl = self.get_output_hot(only_network=False)
        sc_stack = self.conn.orchestration.find_stack(self.name)
        self.heat_client.stacks.update(stack_id=sc_stack.id,
                                       template=hot_tpl)
        if wait_complete:
            self._wait_creation_complete(
                self.name, status='UPDATE_COMPLETE'
            )

    @utils.deprecated
    def create(self, wait_complete=True, interval=3, timeout=600):
        """Create server chain using HEAT

        :param wait_complete (Bool): Block until the stack has the status COMPLETE
        """
        logger.debug(
            'Create server chain: %s.' % self.name
        )
        hot_str = self.get_output_hot()
        self.heat_client.stacks.create(stack_name=self.name,
                                       template=hot_str)
        if wait_complete:
            total_time = 0
            while total_time < timeout:
                sc_stack = self.conn.orchestration.find_stack(self.name)
                # Not created in the db
                if not sc_stack:
                    time.sleep(interval)
                    total_time += interval
                    continue
                elif sc_stack.status == 'CREATE_COMPLETE':
                    return
                # Create in process
                else:
                    logger.debug(
                        'Server chain: %s creation is in progress.',
                        self.name
                    )
                    time.sleep(interval)
                    total_time += interval
            raise SFCRscError(
                'Creation of server chain:%s timeout!' % self.name)

    def delete(self, wait_complete=True, interval=3, timeout=600):
        logger.debug(
            'Delete server chain: %s' % self.name
        )
        sc_stack = self.conn.orchestration.find_stack(self.name)
        if not sc_stack:
            raise SFCRscError('Can not find server chain with name: %s' %
                              self.name)
        self.conn.orchestration.delete_stack(sc_stack)

        if wait_complete:
            total_time = 0
            while total_time < timeout:
                sc_stack = self.conn.orchestration.find_stack(self.name)
                # Delete in progress
                if sc_stack:
                    time.sleep(interval)
                    total_time += interval
                else:
                    return
            raise SFCRscError(
                'Deletion of server chain:%s timeout!' % self.name)


class PortChain(object):

    """Port chain

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
        self.conn = connection.Connection(**auth_args)
        self.pc_client = netsfc_clt.SFCClient(auth_args, logger)

        self.name = name
        self.desc = desc
        self.srv_chain = srv_chain
        self.flow_conf = flow_conf

    def create(self):
        """Create port chain"""
        logger.debug('Create port pairs and port pair groups for %s.'
                     % self.name)
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
        logger.debug('Create the flow classifier.')
        self.pc_client.create('flow_classifier', self.flow_conf)
        fc_id = self.pc_client.get_id(
            'flow_classifier', self.flow_conf['name'])

        pc_args = {
            'name': self.name,
            'description': self.desc,
            'port_pair_groups': pp_grp_id_lst,
            'flow_classifiers': [fc_id]
        }
        logger.debug('Create the port chain: %s.' % self.name)
        self.pc_client.create('port_chain', pc_args)

    def delete(self):
        """Delete the port chain"""
        logger.debug('Delete the port chain: %s' % self.name)
        # Delete port chain
        self.pc_client.delete('port_chain', self.name)

        logger.debug('Delete the flow classifier.')
        self.pc_client.delete('flow_classifier', self.flow_conf['name'])

        # Delete all port pair groups
        logger.debug('Delete port pair groups and port pairs for %s'
                     % self.name)
        srv_ppgrp_lst = self.srv_chain.get_srv_ppgrp_id()
        for grp_idx in range(len(srv_ppgrp_lst)):
            pp_grp_name = 'pp_grp_%s' % grp_idx
            self.pc_client.delete('port_pair_group', pp_grp_name)

        # Delete all port pairs
        for grp_idx, pp_grp in enumerate(srv_ppgrp_lst):
            for pp_idx in range(len(pp_grp)):
                pp_name = 'pp_%s_%s' % (grp_idx, pp_idx)
                self.pc_client.delete('port_pair', pp_name)


class SFC(object):

    """Service Function Chain"""

    def __init__(self, name, desc, srv_chn, port_chn):
        self.name = name
        self.desc = desc
        self.srv_chn = srv_chn
        self.port_chn = port_chn
