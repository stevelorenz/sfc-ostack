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
import time
from functools import partial

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
    """

    def __init__(self, auth_args,
                 mgr_ip='127.0.0.1', mgr_port=6666,
                 ssh_access=True, log_creation_ts=False
                 ):
        """Init a StaticSFCManager

        :param mgr_ip (str): IP address for SF management
        :param mgr_port (int): Port for SF management
        :param auth_args (dict)
        :param log_creation_ts (Bool): If True, time stamps for creation of SFC
        are returned by create_sfc function.
        """
        logger.debug('Init StaticSFCManager on %s:%s' % (mgr_ip, mgr_port))
        self.mgr_ip = mgr_ip
        self.mgr_port = mgr_port
        self.ssh_access = ssh_access
        self.log_creation_ts = log_creation_ts

        self.conn = connection.Connection(**auth_args)

        self.hyper_name_lst = [hyper.name for hyper in
                               self.conn.compute.hypervisors()]

        # MARK: CAN be set in the nova.conf in compute node
        self.cpu_allocate_ratio = 1

    # --- Bad coded functions only used for demo tests and basic algorithms ---
    # Problem:
    #   - Mix usage of pythonsdk and client lib
    #   - Assume all SF instances can be reordered
    # MUST be reimplemented by Zuo
    # -------------------------------------------------------------------------------
    # -------------------------------------------------------------------------------
    def _calc_hyperable_num(self, hyper_name, flavor_name):
        """Calculate the number of allocatable instance on a hypervisor"""
        # MARK: Assume single hypervisor on single host
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

    def _alloc_srv_chn(self, srv_chn, method, dst_hyper_name):
        """MARK: Bad hard-coded only used for tests"""
        if method == 'nova_scheduler':
            for srv_grp in srv_chn:
                for srv in srv_grp:
                    # Nova can do everything...
                    srv['availability_zone'] = 'nova'

        elif method == 'fill_dst':
            sf_num = len(srv_chn)
            flavor_name = srv_chn[0][0]['flavor']
            # Assume other host are equal
            hyper_lst = self.hyper_name_lst.copy()
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
                    for srv in srv_chn[idx]:
                        srv['availability_zone'] = 'nova:%s' % hyper_name
                    allocated += 1
                    logger.debug('Allocate %s to %s, already allocated:%d'
                                 % (srv['name'], hyper_name, allocated))
                    if allocated == sf_num:
                        return

        else:
            raise SFCManagerError(
                'Unknown method for availability zone and host allocation!')

    def _get_srv_chn_alloc(self, srv_chn, avail_hypers):
        """Get allocation of server chain on hypervisors

        :return alloc_map (dict):
        """
        alloc_map = {hyper: list() for hyper in avail_hypers}
        for srv_grp in srv_chn:
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

    def _reorder_srv_chn(self, method, srv_chn, avail_hypers):
        """
        MARK: Assume all SF servers CAN be reordered, only for tests
        """
        new_srv_chn = list()

        if method == 'default':
            new_srv_chn = srv_chn.copy()
            return new_srv_chn

        elif method == 'min_lat':
            logger.info('Reorder the chain for minimal latency')
            alloc_map = self._get_srv_chn_alloc(srv_chn, avail_hypers)
            for hyper, srvs in alloc_map.items():
                new_srv_chn.extend(srvs)
            return new_srv_chn
        else:
            raise SFCManagerError(
                'Unknown reordering method for server chain'
            )
    # -------------------------------------------------------------------------------
    # -------------------------------------------------------------------------------

    def _wait_sf(self, srv_chn, interval=3):
        """Wait for SF program to be ready"""
        # srv_fips = srv_chn.get_srv_fips()
        # check_ips = list()
        # for grp_fips in srv_fips:
        # check_ips.extend(grp_fips)

        check_num = srv_chn.get_srv_num()
        logger.debug('Total number of SF servers: %d' % check_num)

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
                '[StaticSFCManager] Recv ready - packet from %s, %d SF(s)to be ready'
                % (addr[0], check_num)
            )
            logger.debug(debug_info)
            # time.sleep(interval)

    def create_sfc(self, sfc_conf,
                   alloc_method, chain_method, dst_hyper_name,
                   wait_complete=False, wait_sf=True):
        """Create a SFC

        :param sfc_conf:
        :param method(str):
        :param wait_complete (Bool):
        :param wait_sf (Bool):
        """

        if wait_complete and wait_sf:
            raise SFCManagerError(
                'Flag wait_complete conflicts with wait_sf in current implementation.')

        if alloc_method not in ('nova_scheduler', 'fill_dst'):
            raise SFCManagerError('Unknown allocation method for SF servers.')

        if chain_method not in ('default', 'min_lat'):
            raise SFCManagerError('Unknown chaining method for SF servers')

        sfc_name = sfc_conf.function_chain.name
        sfc_desc = sfc_conf.function_chain.description
        logger.info(
            'Create SFC:%s, description:%s. Allocation method:%s, chaining method:%s'
            % (sfc_name, sfc_desc, alloc_method, chain_method))

        self._alloc_srv_chn(sfc_conf.server_chain,
                            alloc_method, dst_hyper_name)

        srv_chn = resource.ServerChain(
            sfc_conf.auth,
            sfc_name + '_srv_chn',
            sfc_desc,
            sfc_conf.network,
            sfc_conf.server_chain,
            self.ssh_access, 'pt'
        )
        srv_chn_start = time.time()
        logger.info(
            'Create server chain, wait_complete=%s.' % wait_complete)
        srv_chn.create(wait_complete=wait_complete)

        if wait_sf:
            logger.info('Wait all SF(s) to be ready via socket.')
            self._wait_sf(srv_chn)
        srv_chn_end = time.time()

        new_srv_chn = self._reorder_srv_chn(
            chain_method,
            sfc_conf.server_chain,
            sfc_conf.function_chain.available_hypervisors
        )

        srv_chn = resource.ServerChain(
            sfc_conf.auth,
            sfc_name + '_srv_chn',
            sfc_desc,
            sfc_conf.network,
            new_srv_chn,
            self.ssh_access, 'pt'
        )

        port_chn = resource.PortChain(
            sfc_conf.auth,
            sfc_name + '_port_chn',
            sfc_desc,
            srv_chn,
            sfc_conf.flow_classifier
        )
        port_chn_start = time.time()
        logger.info('Create port chain.')
        port_chn.create()
        port_chn_end = time.time()

        if self.log_creation_ts:
            return (
                resource.SFC(sfc_name, sfc_desc, srv_chn, port_chn),
                (srv_chn_start, srv_chn_end, port_chn_start, port_chn_end)
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

    def get_hyper_alloc(self, sfc):
        """Get allocation mapping for SF server and hypervisor

        :param sfc (sfc.resources.SFC):
        """
        pass

    def cleanup(self, sfc):
        self.delete_sfc(sfc)


class DynamicSFCManager(BaseSFCManager):

    """SFC manager for dynamic SFC"""

    pass
