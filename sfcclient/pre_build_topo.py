#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
"""
About : Pre-steps before building the test topology, including creation of
a ubuntu-cloud image, a key-pair and a security group.

Email : xianglinks@gmail.com
"""

import glob
import os

from openstack import connection

from const import AUTH_ARGS, SSH_KEYPAIR_NAME

####################
#  ENV Parameters  #
####################

# Path of the ubuntu cloud image
UBUNTU_CLOUD_IMAGE_PATH = os.getenv(
    'HOME') + '/ostack_image/ubuntu-trusty-customized.qcow2'
UBUNTU_CLOUD_IMAGE_NAME = 'ubuntu-cloud'

SECGRP_NAME = 'test'


################
#  Util Funcs  #
################

def pre_build_topo():
    """pre_build_topo"""
    print('# Create a connection to the cloud with Auth UTL: %s' %
          AUTH_ARGS['auth_url'])
    conn = connection.Connection(**AUTH_ARGS)

    if not conn.image.find_image(UBUNTU_CLOUD_IMAGE_NAME):
        print("[IMAGE] Upload customized ubuntu-cloud image...")
        data = open('/opt/stack/ostack_image/ubuntu-trusty-customized.qcow2',
                    'rb').read()
        image_attrs = {
            'name': UBUNTU_CLOUD_IMAGE_NAME,
            'data': data,
            'disk_format': 'qcow2',
            'container_format': 'bare',
            'visibility': 'public',
        }
        conn.image.upload_image(**image_attrs)

    if not conn.compute.find_keypair(SSH_KEYPAIR_NAME):
        print("[KEYPAIR] Create Key Pair: %s" % SSH_KEYPAIR_NAME)
        key_pair = conn.compute.create_keypair(name=SSH_KEYPAIR_NAME)
        # remove old pem files
        for key_file in glob.glob('./*.pem'):
            os.chmod(key_file, 0o777)
            os.remove(key_file)

        with open('./%s.pem' % SSH_KEYPAIR_NAME, 'w+') as key_file:
            key_file.write("%s" % key_pair.private_key)
            os.chmod('./%s.pem' % SSH_KEYPAIR_NAME, 0o400)

    if not conn.network.find_security_group(SECGRP_NAME):
        project = conn.identity.find_project(AUTH_ARGS['project_name'])
        print('[SECGRP] Create a test security group...')
        sec_gp = conn.network.create_security_group(
            name=SECGRP_NAME, project_id=project.id,
            description='Only for testing, allow all ICMP, TCP and UDP ingress access'
        )
        print('[SECGRP] Add rules, allow ICMP, TCP and UDP ingress for all addresses...')
        for ptl in ('icmp', 'tcp', 'udp'):
            conn.network.create_security_group_rule(
                security_group_id=sec_gp.id,
                direction='ingress',
                # allow all ip addresses
                remote_ip_prefix='0.0.0.0/0',
                protocol=ptl,
                port_range_max=None,
                port_range_min=None,
                ethertype='IPv4')


if __name__ == "__main__":
    pre_build_topo()
