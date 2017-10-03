#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Run UDP latency measurements

Email: xianglinks@gmail.com
"""

import os
import subprocess
import time

import paramiko
from openstack import connection

# Addr of the UDP echo-server
SERVER_ADDR = "192.168.100.200:9999"
# UDP client parameters
# NUM_PACKETS = '10000'
NUM_PACKETS = '10'
SEND_RATE = '1000'  # byte/s
PAYLOAD_LEN = '512'  # byte

# Minimal and maximal number of SF instances
MIN_SF_NUM = 2
MAX_SF_NUM = 2

SSH_PKEY = '/home/zuo/sfc_ostack_test/sfc_test.pem'

DROPBOX_TOOL = '~/bin/dbxcli-linux-amd64'


auth_args = {
    'auth_url': 'http://192.168.100.1/identity/v3',
    'project_name': 'admin',
    'user_domain_name': 'default',
    'project_domain_name': 'default',
    'username': 'admin',
    'password': 'stack',
}

conn = connection.Connection(**auth_args)


def _get_floating_ip(pt_name):
    ins_port = conn.network.find_port(pt_name)
    fip = list(conn.network.ips(port_id=ins_port.id))[0].floating_ip_address
    return fip


def py_forwarding_test():
    """Test python forwarding"""
    for srv_num in range(MIN_SF_NUM, MAX_SF_NUM + 1):
        print('[TEST] Create %d SF servers' % srv_num)
        subprocess.run(['python3', './sfc_mgr.py', 'c', '%d' %
                        srv_num], check=True)
        time.sleep(5)
        try:
            os.remove('/home/zuo/.ssh/known_hosts')
        except Exception:
            pass
        # Copy and run forwarding program via SSH
        ssh_clt = paramiko.SSHClient()
        # Allow connection not in the known_host
        ssh_clt.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        for ins_num in range(1, srv_num + 1):
            print('[TEST] Copy and run SF program on server: chn%d' % ins_num)
            pt_name = 'chn%d_pt' % ins_num
            fip = _get_floating_ip(pt_name)
            while True:
                try:
                    ssh_clt.connect(fip, 22, 'ubuntu',
                                    key_filename=SSH_PKEY)
                except Exception:
                    print(
                        '[Error] Can not connect %s, Try again after 3 seconds...' % fip)
                    time.sleep(3)
                else:
                    print('[DEBUG] Connect to %s succeeded' % fip)
                    break
            sftp_clt = ssh_clt.open_sftp()
            sftp_clt.put('./udp_forwarding.py',
                         '/home/ubuntu/udp_forwarding.py')
            transport = ssh_clt.get_transport()
            # Try multiple times...
            # Sometime the forwarding process is not running, i don't know why.
            for i in range(5):
                channel = transport.open_session()
                print('[DEBUG] Run python forwarder.')
                while True:
                    channel.exec_command(
                        'nohup python3 /home/ubuntu/udp_forwarding.py > /dev/null 2>&1 &'
                    )
                    status = channel.recv_exit_status()
                    print('[DEBUG] forwarder process status: %d' % status)
                    # Process runs successfully
                    if status == 0:
                        break
            time.sleep(5)
            # import ipdb
            # ipdb.set_trace()
            # TODO: Check if the process is really running
            sftp_clt.close()
            ssh_clt.close()

        # Run UDP client
        time.sleep(5)
        print('[TEST] Run UDP client')
        OUTPUT_FILE_NAME = "./pyf-%s-%s-%s-%s.csv" % (
            NUM_PACKETS, SEND_RATE, PAYLOAD_LEN, srv_num)
        subprocess.run(['python3', './udp_latency.py', '-c', SERVER_ADDR,
                        '--n_packets', NUM_PACKETS,
                        '--payload_len', PAYLOAD_LEN,
                        '--send_rate', SEND_RATE,
                        '--output_file', OUTPUT_FILE_NAME
                        ],
                       check=True)
        time.sleep(5)
        subprocess.run(['python3', './sfc_mgr.py', 'd', '%d' %
                        srv_num], check=True)


def lk_forwarding_test():
    """Test linux kernel forwarding"""
    pass


if __name__ == "__main__":
    py_forwarding_test()
    # lk_forwarding_test()
