#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: SFC Resource Manager

Email: xianglinks@gmail.com
"""

import logging
import socket
import time

from sfcostack import conf, log
from sfcostack.sfc import resource

logger = log.logger


class SFCManagerError(Exception):
    """SFC manager error"""
    pass


def get_sfc_manager(typ):
    """Get SFC manager object

    :param typ (str): Type of the SFC manager
    """
    if typ == 'static':
        return StaticSFCManager

    else:
        raise SFCManagerError('Unknown SFC manager type!')


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

    def __init__(self, mgr_ip='127.0.0.1', mgr_port=6666,
                 ssh_access=True, log_creation_ts=False
                 ):
        """Init a StaticSFCManager

        :param mgr_ip (str): IP address for SF management
        :param mgr_port (int): Port for SF management
        :param log_creation_ts (Bool): If True, time stamps for creation of SFC
        are returned by create_sfc function.
        """
        logger.debug('Init StaticSFCManager on %s:%s' % (mgr_ip, mgr_port))
        self.mgr_ip = mgr_ip
        self.mgr_port = mgr_port
        self.ssh_access = ssh_access
        self.log_creation_ts = log_creation_ts

        self.sfc_que = list()

    def create_sfc(self, sfc_conf, wait_complete=False, wait_sf=True):
        sfc_name = sfc_conf.function_chain.name
        sfc_desc = sfc_conf.function_chain.description
        logger.info('Create SFC:%s, description:%s' % (sfc_name, sfc_desc))
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

    def cleanup(self, sfc):
        self.delete_sfc(sfc)

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


class DynamicSFCManager(BaseSFCManager):

    """SFC manager for dynamic SFC"""

    pass
