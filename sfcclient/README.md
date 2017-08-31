# OpenStack-SFC Client Module #

A Python REST-client(single file module) for OpenStack
[networking-sfc](https://docs.openstack.org/networking-sfc/latest/) neutron extension.

The official documentation of this extension currently *only* provides command-line interface, which makes it difficult
to use this extension in a Python based project. This module implements a wrapper client for SFC(Service Function
    Chaining) operations based on provided REST APIs.

Programming Language: Python 3.5.2

## Catalog ##

#### [sfcclient.py](./sfcclient.py)

A REST-client for using networking-sfc APIs

#### [test_demo](./test_demo)

A test demo for testing networking-sfc and sfc-client module. Details can be found in the README of the demo folder.

#### requirements.txt and dev_requirements.txt

Python package requirements for using and development of sfcclient

## Usage ##

1. Install the dependencies in the requirements.txt
2. Copy sfcclient.py in the project properly
3. Check the docstring and comments in the [sfcclient.py](./sfcclient.py) and [example.py](./example.py).

### Arguments Format ###

TODO

## Main Reference ##

- [openstack/python-keystoneclient](https://github.com/openstack/python-keystoneclient)
- [openstack/python-novaclient](https://github.com/openstack/python-novaclient)
