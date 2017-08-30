#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
"""
About : Steps after finishing building the test topology

        1. Get and store all floating IPs of instances(./remote_instance.txt)
        2. Config VMs for chaining via SSH

Email : xianglinks@gmail.com
"""

import time

import paramiko
from openstack import connection

import conf


def _get_sshclient(host_name, ip, port=22):
    """Get a paramiko SSH client object"""
    ssh_clt = paramiko.SSHClient()
    # Allow connection not in the known_host
    ssh_clt.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_clt.connect(ip, port, host_name,
                    key_filename=conf.SSH_KEY_ARGS['path'])
    return ssh_clt


def get_topo_info():
    """Get topology parameters

    :rtype: dict
    """
    topo_info = dict()
    conn = connection.Connection(**conf.AUTH_ARGS)

    for ins in ['src', 'dst', 'chn1', 'chn2', 'chn3']:
        pt = conn.network.find_port(ins + '_pt')
        topo_info[ins + '_pt_id'] = pt.id
        topo_info[ins + '_ip'] = list(conn.network.ips(port_id=pt.id))[0].fixed_ip_address

    for ins in ['chn1', 'chn2', 'chn3']:
        for dr in ['in', 'out']:
            pt = conn.network.find_port(ins + '_pt_' + dr)
            topo_info[ins + '_pt_' + dr + '_id'] = pt.id

    return topo_info


def _config_chn_ins(ssh_clt, topo_info):
    """Config chain instances via SSH"""
    # MARK: Assume the iterface name pattern: eth0, eth1, eth2...
    for ifce_name in ['eth1', 'eth2']:
        print('## Setup interface: %s' % ifce_name)
        ssh_clt.exec_command('sudo ip link set %s up' % ifce_name)
        time.sleep(1)
        print('## Assign IP via DHCP')
        ssh_clt.exec_command('sudo dhclient %s' % ifce_name)
        time.sleep(1)
        print('## Remove duplicate route table items...')
        ssh_clt.exec_command('sudo ip route delete %s dev %s'
                             % (conf.NET_ARGS['pvt_subnet_cidr'], ifce_name)
                             )
        time.sleep(1)

    print('## Add static routing to source and destination...')
    ssh_clt.exec_command('sudo ip route add %s dev eth1' % topo_info['src_ip'])
    time.sleep(1)
    ssh_clt.exec_command('sudo ip route add %s dev eth2' % topo_info['dst_ip'])
    time.sleep(1)

    print('## Enable Linux Kernel IP forwarding...')
    ssh_clt.exec_command('echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward')
    time.sleep(1)
    print('# Config Finished\n')


def post_build_topo():
    conn = connection.Connection(**conf.AUTH_ARGS)

    print('# Get and store floating IPs of all instances...')
    INS_LST = ['src', 'dst', 'chn1', 'chn2', 'chn3']
    fip_dt = dict()
    for ins in INS_LST:
        ins_port = conn.network.find_port(ins + '_pt')
        fip_dt[ins] = list(conn.network.ips(port_id=ins_port.id))[0].floating_ip_address
    with open(conf.INS_ARGS['host_file'], 'w+') as host_file:
        host_file.write('\n'.join(fip_dt.values()))

    # Config all chain instances via SSH
    topo_info = get_topo_info()
    for chn in ['chn1', 'chn2', 'chn3']:
        print('# Config %s with IP: %s' % (chn, fip_dt[chn]))
        ssh_clt = _get_sshclient('ubuntu', fip_dt[chn])
        _config_chn_ins(ssh_clt, topo_info)


if __name__ == "__main__":
    post_build_topo()
