# OpenStack-SFC Client Module #

A client lib for OpenStack [networking-sfc](https://docs.openstack.org/networking-sfc/latest/) neutron extension.

The official documentation of this extension currently *only* provides command-line interface, which makes it difficult
to use this extension in a relative complex OpenStack application. This module implements wrapper classes for
SFC(Service Function Chaining) operations based on the REST API provided by the
[networking-sfc](https://docs.openstack.org/networking-sfc/latest/) extension.

Programming Language: Python 3.5.2

## Catalog ##

- test demo

A simple test demo for testing networking-sfc and sfc-client module. Details can be found in the README of the demo
folder.


- sfcclient.py

A REST client for using networking-sfc APIs


- requirements.txt and dev_requirements.txt

Python package requirements for using and development of sfcclient


## Usage ##

Check the docstring and comments in the [sfcclient.py](./sfcclient.py).

### Arguments Format ###

TODO

## Main Reference ##

- [openstack/python-keystoneclient](https://github.com/openstack/python-keystoneclient)
- [openstack/python-novaclient](https://github.com/openstack/python-novaclient)
