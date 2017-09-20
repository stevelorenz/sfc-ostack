#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
"""
About : Cloud Configs

    Pre-steps before building the test topology
        - Upload ubuntu-cloud image
        - Create a SSH key-paris

Email : xianglinks@gmail.com
"""

import glob
import os

from openstack import connection


def pre_build_topo():
    """pre_build_topo"""

    auth_args = {
        # 'auth_url': 'http://192.168.100.1/identity/v3',
        'auth_url': 'http://192.168.0.100/identity/v3',
        'project_name': 'admin',
        'user_domain_name': 'default',
        'project_domain_name': 'default',
        'username': 'admin',
        'password': 'stack',
    }

    print('# Create a connection to the cloud with Auth URL: %s' %
          auth_args['auth_url'])
    conn = connection.Connection(**auth_args)

    img_args = {
        'name': 'ubuntu-cloud',
        # Path of the image
        'path': os.getenv('HOME') + '/ostack_image/ubuntu-trusty-customized.qcow2',
        'disk_format': 'qcow2',
        'container_format': 'bare',
        'visibility': 'public',
    }
    if not conn.image.find_image(img_args['name']):
        print("[IMAGE] Upload %s image..." % img_args['name'])
        data = open(img_args['path'], 'rb').read()
        image_attrs = {
            'name': img_args['name'],
            'data': data,
            'disk_format': img_args['disk_format'],
            'container_format': img_args['container_format'],
            'visibility': img_args['visibility'],
        }
        conn.image.upload_image(**image_attrs)

    kp_args = {
        'name': 'sfc_test',
        'path': './sfc_test.pem'
    }
    if not conn.compute.find_keypair(kp_args['name']):
        print("[KEYPAIR] Create Key Pair: %s" % kp_args['name'])
        key_pair = conn.compute.create_keypair(name=kp_args['name'])
        # remove old pem files
        for key_file in glob.glob('./*.pem'):
            os.chmod(key_file, 0o777)
            os.remove(key_file)

        with open(kp_args['path'], 'w+') as key_file:
            key_file.write("%s" % key_pair.private_key)
            os.chmod('./%s.pem' % kp_args['name'], 0o400)

    sec_grp_args = {
        'name': 'sfc_test'
    }
    if not conn.network.find_security_group(sec_grp_args['name']):
        project = conn.identity.find_project(auth_args['project_name'])
        print('[SECGRP] Create a test security group: %s...' %
              sec_grp_args['name'])
        sec_gp = conn.network.create_security_group(
            name=sec_grp_args['name'], project_id=project.id,
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

    fv_args = {
        'name': 'sfc_test',
        'vcpus': '1',
        # in GB, for ubuntu-cloud minimal 1.8G
        'disk': '2',
        # in MB
        'ram': '1024'
    }
    if not conn.compute.find_flavor(fv_args['name']):
        print('[FLAVOR] Create a flavor for testing instances: %s...'
              % fv_args['name'])
        conn.compute.create_flavor(**fv_args)


if __name__ == "__main__":
    pre_build_topo()
