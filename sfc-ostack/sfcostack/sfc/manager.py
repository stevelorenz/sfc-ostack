#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: SFC Resource Manager

Email: xianglinks@gmail.com
"""

import logging
import random
import socket
import threading
import time
from functools import partial

import paramiko
from openstack import connection

from sfcostack import conf, log
from sfcostack.dev import helper
from sfcostack.sfc import resource

logger = log.logger


def get_sfc_manager(typ):
    """Get SFC manager object

    :param typ (str): Type of the SFC manager
    """
    if typ == 'static':
        return StaticSFCManager

    else:
        raise SFCManagerError('Unknown SFC manager type!')


###########
#  Error  #
###########

class SFCManagerError(Exception):
    """SFC manager error"""
    pass


#############
#  Manager  #
#############

class BaseSFCManager(object):

    """Base class for all SFC resource managers"""

    def create_sfc(self, sfc_conf):
        """Create SFC with given sfc_conf

        :param sfc_conf (sfcostack.conf.SFCConf): SFC arguments
        """
        raise NotImplementedError()

    def delete_sfc(self, sfc):
        """Delete given SFC

        :param sfc (sfc.resource.SFC):
        """
        raise NotImplementedError()

    def update_sfc(self, sfc, sfc_conf):
        """Update SFC with new sfc_conf"""
        raise NotImplementedError()

    def cleanup(self, sfc):
        """Cleanup created SFC"""
        raise NotImplementedError()


class StaticSFCManager(BaseSFCManager):

    """SFC manager for static SFC

    Static means the SFC CAN not be updated

    MARK:
        Do not support port pair group feature
    """

    def __init__(self, auth_args,
                 mgr_ip='127.0.0.1', mgr_port=6666,
                 ssh_access=True, return_ts=False, log_ts=True
                 ):
        """Init a StaticSFCManager

        :param mgr_ip (str): IP address for SF management
        :param mgr_port (int): Port for SF management
        :param auth_args (dict)
        """
        logger.debug(
            'Init StaticSFCManager, management addr: %s:%s', mgr_ip, mgr_port)
        self.mgr_ip = mgr_ip
        self.mgr_port = mgr_port
        self.ssh_access = ssh_access
        self.return_ts = return_ts
        self.log_ts = log_ts

        # --- Stack API and SSH client ---
        self.conn = connection.Connection(**auth_args)
        self.ssh_clt = paramiko.SSHClient()
        self.ssh_clt.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # --- Nova compute resources ---
        self.all_hypers = [hyper.name for hyper in
                           self.conn.compute.hypervisors()]
        # MARK: CAN be set in the nova.conf in compute node
        self.cpu_allocate_ratio = 1

    # --- Bad coded functions only used for demo tests and basic algorithms ---
    # Problem:
    #   - Can not get data of physicial topology
    #   - Assume all SF instances can be reordered
    # MUST be reimplemented by Zuo
    # -------------------------------------------------------------------------------
    # -------------------------------------------------------------------------------
    def _alloc_srv_chn(self, method, srv_chn_conf, avail_zone,
                       dst_hyper_name, avail_hypers):
        """Allocate server chain on hypervisors"""
        if method == 'nova_default':
            for srv_grp in srv_chn_conf:
                for srv in srv_grp:
                    # Nova scheduler can do everything...
                    srv['availability_zone'] = avail_zone

        elif method == 'fill_one':
            sf_num = len(srv_chn_conf)
            flavor_name = srv_chn_conf[0][0]['flavor']
            # Assume other host are equal
            hyper_lst = avail_hypers.copy()
            hyper_lst.remove(dst_hyper_name)
            hyper_lst.insert(0, dst_hyper_name)
            hyper_ins_num = [self._calc_hyperable_num(hyper_name, flavor_name)
                             for hyper_name in hyper_lst]
            debug_str = 'hyper list: ' + ','.join(hyper_lst)
            debug_str += ', hyper_ins_num: ' + \
                ','.join(map(str, hyper_ins_num))

            if sum(hyper_ins_num) < sf_num:
                raise SFCManagerError(
                    'Insufficient resource for allocation of SF servers')
            allocated = 0
            for ins_num, hyper_name in zip(hyper_ins_num, hyper_lst):
                for idx in range(allocated, allocated + ins_num):
                    for srv in srv_chn_conf[idx]:
                        srv['availability_zone'] = 'nova:%s' % hyper_name
                    allocated += 1
                    logger.debug('Allocate %s to %s, already allocated:%d'
                                 % (srv['name'], hyper_name, allocated))
                    if allocated == sf_num:
                        return

    def _reorder_srv_chn(self, method, srv_chn_conf, avail_hypers):
        """Reorder the srv_chn_conf according to the priority in avail_hypers"""
        reorder_srv_chn_conf = list()
        if method == 'min_lat':
            alloc_map = self._get_srv_chn_alloc(srv_chn_conf, avail_hypers)

            for hyper in avail_hypers:
                for srv in alloc_map[hyper]:
                    reorder_srv_chn_conf.append([srv])

            return reorder_srv_chn_conf
    # -------------------------------------------------------------------------------
    # -------------------------------------------------------------------------------

    def _calc_hyperable_num(self, hyper_name, flavor_name):
        """Calculate the number of allocatable instance on a hypervisor"""
        hyper_id = self.conn.compute.find_hypervisor(hyper_name).id
        hyper = self.conn.compute.get_hypervisor(hyper_id)
        flavor_id = self.conn.compute.find_flavor(flavor_name).id
        flavor = self.conn.compute.get_flavor(flavor_id)
        num_cpu = int(
            self.cpu_allocate_ratio *
            (hyper.vcpus - hyper.vcpus_used) / flavor.vcpus
        )
        num_ram = int(hyper.memory_free / flavor.ram)
        num_disk = int(hyper.disk_available / flavor.disk)
        logger.debug('Hyper:%s, flavor:%s, cpu:%d, ram:%d, disk:%d'
                     % (hyper.name, flavor.name, num_cpu, num_ram, num_disk))

        return min(num_cpu, num_ram, num_disk)

    def _get_srv_chn_alloc(self, srv_chn_conf, avail_hypers):
        """Get allocation of server chain on available hypervisors

        :return alloc_map (dict):
        """
        alloc_map = {hyper: list() for hyper in avail_hypers}
        for srv_grp in srv_chn_conf:
            for srv in srv_grp:
                while True:
                    srv_tmp = self.conn.compute.find_server(srv['name'])
                    if srv_tmp:
                        break
                    else:
                        logger.debug('Server:%s can not be found in the db' %
                                     srv['name'])
                        time.sleep(1)
                srv_obj = self.conn.compute.get_server(srv_tmp)
                alloc_map[srv_obj.hypervisor_hostname].append(srv)
        return alloc_map

    @staticmethod
    def _get_alloc_map_str(alloc_map):
        map_str = ''
        for hyper, srv_lst in alloc_map.items():
            map_str += '%s: ' % hyper
            map_str += ','.join(
                (srv['name'] for srv in srv_lst)
            )
            map_str += ';'
        return map_str

    # --- Chaining Management ---

    # --- SFC CRUD ---

    def create_sfc(self, sfc_conf,
                   alloc_method, chain_method,
                   wait_sf_ready=True, wait_method='udp_packet'):
        """Create a SFC using given allocation and chaining method

        :param sfc_conf ():
        :param alloc_method (str): Method for instance allocation
        :param chain_method (str): Method for chaining instances
        :param wait_sf_ready (Bool): If True, the manager blocks until all SF
                                     programs are ready.
        :param wait_method (str): Method for waiting SF programs
        """

        if alloc_method not in ('nova_default', 'fill_one'):
            raise SFCManagerError('Unknown allocation method for SF servers.')

        if chain_method not in ('default', 'min_lat'):
            raise SFCManagerError('Unknown chaining method for SF servers')

        sfc_name = sfc_conf.function_chain.name
        sfc_desc = sfc_conf.function_chain.description
        time_info = list()
        logger.info(
            'Create SFC: %s, description: %s. Allocation method: %s, chaining method :%s'
            % (sfc_name, sfc_desc, alloc_method, chain_method))

        start_ts = time.time()
        self._alloc_srv_chn(
            alloc_method,
            sfc_conf.server_chain,
            sfc_conf.function_chain.availability_zone,
            sfc_conf.function_chain.destination_hypervisor,
            sfc_conf.function_chain.available_hypervisors
        )

        srv_chn = resource.ServerChain(
            sfc_conf.auth,
            sfc_name + '_srv_chn',
            sfc_desc,
            sfc_conf.network,
            sfc_conf.server_chain,
            self.ssh_access, 'pt'
        )

        logger.info('Create server chain: %s', srv_chn.name)
        # MARK: Create networking and instance resources separately

        srv_chn.create_network()

        if wait_sf_ready:
            logger.info('Wait all SF(s) to be ready with method: %s.',
                        wait_method)
            wait_sf_thread = threading.Thread(
                target=self._wait_sf_ready,
                args=(srv_chn, wait_method)
            )
            wait_sf_thread.start()
        else:
            logger.warn(
                (
                    'Do not wait for SF(s) to be ready. '
                    'Instances creation are not completed. '
                    'This is not recommeded!'
                )
            )

        srv_chn.create_instance(wait_complete=True)
        # Server chain launching time
        time_info.append(time.time() - start_ts)
        # Block main thread until all SFs are ready
        logger.info(
            'All server instances are launched, waiting for SF programs')
        if wait_sf_ready:
            start_ts = time.time()
            wait_sf_thread.join()
            # Waiting time for SF program
            time_info.append(time.time() - start_ts)
        else:
            time_info.append(0)

        # Log server chain allocation mapping
        alloc_map = self._get_srv_chn_alloc(
            sfc_conf.server_chain,
            self.all_hypers
        )
        logger.info(
            'Allocation mapping: %s', self._get_alloc_map_str(alloc_map)
        )

        if chain_method == 'min_lat':
            start_ts = time.time()
            if alloc_method != 'nova_default':
                raise SFCManagerError(
                    'Chaining method min_lat only support allocation method nova_default'
                )
            logger.info('Reorder server chain with simple min_lat method')
            logger.debug(
                'Before reorder: %s', ','.join(
                    (srv_grp[0]['name'] for srv_grp in sfc_conf.server_chain)
                )
            )
            reorder_srv_chn_conf = self._reorder_srv_chn(
                chain_method,
                sfc_conf.server_chain,
                sfc_conf.function_chain.available_hypervisors
            )

            logger.debug(
                'After reorder: %s', ','.join(
                    (srv_grp[0]['name'] for srv_grp in reorder_srv_chn_conf)
                )
            )

            srv_chn = resource.ServerChain(
                sfc_conf.auth,
                sfc_name + '_srv_chn',
                sfc_desc,
                sfc_conf.network,
                reorder_srv_chn_conf,
                self.ssh_access, 'pt'
            )
            # Time for reorder the chain
            time_info.append(time.time() - start_ts)
        else:
            time_info.append(0)

        port_chn = resource.PortChain(
            sfc_conf.auth,
            sfc_name + '_port_chn',
            sfc_desc,
            srv_chn,
            sfc_conf.flow_classifier
        )
        logger.info('Create port chain: %s', port_chn.name)
        start_ts = time.time()
        port_chn.create()
        # Time for creating port chain
        time_info.append(time.time() - start_ts)

        if self.log_ts:
            logger.info('Time info: %s',
                        ','.join(map(str, time_info)))

        if self.return_ts:
            return (
                resource.SFC(sfc_name, sfc_desc, srv_chn, port_chn),
                time_info
            )

        else:
            return resource.SFC(sfc_name, sfc_desc, srv_chn, port_chn)

    def delete_sfc(self, sfc):
        logger.info(
            'Delete SFC:%s, description:%s' % (sfc.name, sfc.desc)
        )
        sfc.port_chn.delete()
        sfc.srv_chn.delete()

    def update_sfc(self, **args):
        raise RuntimeError(
            "Static SFC manager doesn't support update operation.")

    # --- SF Instance Management ---

    def _try_ssh_connect(self, ssh_tuple, timeout=300, interval=3):
        """TODO"""
        pass

    def _wait_sf_ready(self, srv_chn, method='udp_packet', interval=0.5):
        """Wait for SF conf and programs to be ready"""

        if method == 'udp_packet':
            # Get floating IPs for all SF servers
            fip_lst = srv_chn.get_srv_fips(no_grp=True)
            check_num = len(fip_lst)
            logger.debug(
                'Total number of to be waited SF servers: %d' % check_num
            )
            recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            recv_sock.bind((self.mgr_ip, self.mgr_port))
            recv_sock.settimeout(None)

            # MARK: Timeout MAY be used here
            while True:
                if check_num == 0:
                    break
                _, addr = recv_sock.recvfrom(1024)
                check_num -= 1
                debug_info = (
                    'Recv ready-packet from %s, remain %d SF(s) to be ready'
                    % (addr[0], check_num)
                )
                logger.debug(debug_info)
                time.sleep(interval)

        # TODO: Check if specific file is created on all instances
        elif method == 'file':
            dft_path = '~/.cache/sf_ready.csv'
            raise NotImplementedError
        else:
            raise SFCManagerError(
                'Unknown waiting method for SF(s) to be ready.'
            )

    def cleanup(self):
        pass


class DynamicSFCManager(BaseSFCManager):

    """SFC manager for dynamic SFC"""

    pass
