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
from sfcostack.sfc import allocator, resource

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

    def __init__(self, mgr_ip, mgr_port=6666,
                 ssh_access=True
                 ):
        """Init a StaticSFCManager

        :param mgr_ip (str): IP address for SF management
        :param mgr_port (int): Port for SF management
        """
        logger.debug('Init StaticSFCManager on %s:%s' % (mgr_ip, mgr_port))
        self.mgr_ip = mgr_ip
        self.mgr_port = mgr_port
        self.ssh_access = ssh_access

        self.sfc_que = list()
        # TODO: Get mapping from sfc.allocator
        self.allocator = None
        self.region_mapping = dict()

    def create_sfc(self, sfc_conf, wait_sf=True):
        srv_chn = resource.ServerChain(
            sfc_conf.auth,
            sfc_conf.function_chain.name,
            sfc_conf.function_chain.description,
            sfc_conf.network,
            sfc_conf.server_chain,
            self.ssh_access, 'pt'
        )
        srv_num = srv_chn.get_srv_num()
        # MARK: Do
        srv_chn.create(wait_complete=False)

        if wait_sf:
            logger.info('[StaticSFCManager] Wait all SF(s) to be ready.')
            self._wait_sf(srv_chn)

        port_chn = resource.PortChain(
            sfc_conf.auth,
            sfc_conf.function_chain.name,
            sfc_conf.function_chain.description,
            srv_chn,
            sfc_conf.flow_classifier
        )
        port_chn.create()

        return resource.SFC(srv_chn, port_chn)

    def delete_sfc(self, sfc):
        sfc.port_chn.delete()
        srv_num = sfc.srv_chn.get_srv_num()
        sfc.srv_chn.delete(600 * srv_num)

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

        srv_num = srv_chn.get_srv_num()
        logger.debug('[StaticSFCManager] Wait %d SF server to be ready.' %
                     srv_num)

        recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        recv_sock.bind((self.mgr_ip, self.mgr_port))
        recv_sock.settimeout(None)

        # MARK: Timeout MAY be used here
        while True:
            if srv_num == 0:
                # if len(check_ips) == 0:
                break
            _, addr = recv_sock.recvfrom(1024)
            # check_ips.remove(addr[0])
            srv_num -= 1
            debug_info = (
                '[StaticSFCManager] Recv a ready-packet from %s, %d SF(s)to be ready'
                # % (addr[0], len(check_ips))
                % (addr[0], srv_num)
            )
            logger.debug(debug_info)
            # time.sleep(interval)


class DynamicSFCManager(BaseSFCManager):

    """SFC manager for dynamic SFC"""

    pass
