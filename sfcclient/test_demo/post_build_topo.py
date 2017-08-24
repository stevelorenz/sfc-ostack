#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
"""
About : Steps after the build of the test-topology

        1. Get all floating IPs of instances
        2. Config the chain_vm via SSH

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


def post_build_topo():
    conn = connection.Connection(**conf.AUTH_ARGS)

    print('# Get the floating IPs of the instances...')
    fip_lst = []
    for ins in ('src_vm', 'dst_vm'):
        ins_port = conn.network.find_port(ins)
        ins_fip = list(conn.network.ips(port_id=ins_port.id))[0].floating_ip_address
        fip_lst.append(ins_fip)

    ch_vm_port = conn.network.find_port('chain_vm')
    ch_vm_fip = list(conn.network.ips(port_id=ch_vm_port.id))[0].floating_ip_address
    fip_lst.append(ch_vm_fip)
    print(fip_lst)

    with open(conf.INS_ARGS['host_file'], 'w+') as host_file:
        host_file.write('\n'.join(fip_lst))

    ssh_clt = _get_sshclient('ubuntu', ch_vm_fip)
    print('# Set all interfaces on the chain_vm up...')
    for ifce_num in range(0, 3):
        print('Set iface eth%d up' % ifce_num)
        stdin, stdout, stderr = ssh_clt.exec_command('sudo ip link set eth%d up' % ifce_num)
        time.sleep(1)

    # MARK: Use OVS instead
    # print('# Create a linux bridge on the chain_vm...')
    # ssh_clt.exec_command('sudo brctl addbr br0')
    # ssh_clt.exec_command('sudo brctl brctl addif br0 eth1')
    # ssh_clt.exec_command('sudo brctl brctl addif br0 eth2')
    # time.sleep(0.5)
    # ssh_clt.exec_command('sudo ip link set br0 up')


if __name__ == "__main__":
    post_build_topo()
