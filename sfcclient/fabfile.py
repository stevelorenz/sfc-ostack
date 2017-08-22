#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About : Fabfile for instance administration
Email : xianglinks@gmail.com
"""

from __future__ import with_statement

from re import search
from time import sleep, strftime

from fabric.api import (cd, env, get, local, parallel, put, run, settings,
                        sudo, task)
from fabric.context_managers import hide
from fabric.contrib import project


# Helper Functions
# -----------------------------------------------
def _get_instance_from_file():
    """Get SSH addrs of instances from a text file"""
    ins_lt = list()
    try:
        with open('./remote_instance.txt') as rfile:
            for ins_addr in rfile:
                ins_lt.append(ins_addr.strip())
    except IOError:
        pass

    return ins_lt
# -----------------------------------------------


# Fabric Configurations
# -----------------------------------------------
# number of times for connection
env.connection_attempts = 1
# skip the unavailable hosts
env.skip_bad_hosts = True
env.colorize_errrors = True
# -----------------------------------------------

# Init Remote Hosts and Roles
# -----------------------------------------------
env.roledefs = {
    'instance': _get_instance_from_file()
}

# set default roles
# without -R and -H option, default roles will be used
if not env.roles and not env.hosts:
    env.roles = ['instance']

# use pem private key for SSH
env.key_filename = './test.pem'
# -----------------------------------------------


# Operations
# -----------------------------------------------
@task
@parallel
def upload_shared():
    """Upload shared files for all instances"""
    # default copy to home dir
    put('./instance_shared', '~/')


if __name__ == "__main__":
    print("Please use fabric command-line tool.")


@task
@parallel
def local_cleanup():
    """Run cleanups on local host"""
    print("### Clean all SSH known hosts...")
    local("rm -rf $HOME/.ssh/known_hosts")
    local("rm -rf $HOME/.ssh/known_hosts.old")
    # print("### Clean all local pem private keys...")
    # local("rm -f ./*.pem")
# -----------------------------------------------
