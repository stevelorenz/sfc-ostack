#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About : HEAT Template Constructor
Email : xianglinks@gmail.com

Ref   : 1. Heat Orchestration Template (HOT) specification
        2. openstack/heat-translator
"""

import logging
from collections import OrderedDict

import yaml

from sfcostack.log import logger


class HOTError(Exception):
    """HOT Error"""
    pass


class Parameter(object):

    """HOT Parameter Attr"""

    KEYS = (TYPE, DESCRIPTION, DEFAULT, CONSTRAINTS, HIDDEN, LABEL) = \
        ('type', 'description', 'default', 'constraints', 'hidden', 'label')

    def __init__(self, name, type, label=None, desc=None, default=None):
        """Init a HOT parameter"""
        self.name = name
        self.type = type
        self.label = label
        self.desc = desc
        self.default = default

    def get_output_dict(self):
        """Output a parameter as a nested dict"""
        para = OrderedDict()
        para[self.TYPE] = self.type
        if self.type:
            para[self.TYPE] = self.type
        if self.desc:
            para[self.DESCRIPTION] = self.desc
        if self.default:
            para[self.DEFAULT] = self.default
        if self.label:
            para[self.LABEL] = self.label

        return {self.name: para}


class Output(object):

    """HOT Output Attr"""

    def __init__(self, name, value, desc=None):
        self.name = name
        self.value = value
        self.desc = desc

    def get_output_dict(self):
        if self.desc:
            return {self.name: {'value': self.value,
                                'description': self.desc}}
        return {self.name: {'value': self.value}}


class Resource(object):

    """HOT Resource Attr"""

    SECTIONS = (TYPE, PROPERTIES, MEDADATA, DEPENDS_ON) = \
        ('type', 'properties', 'metadata', 'depends_on')

    RSC_TYPE_MAP = {
        'net': 'OS::Neutron::Net',
        'subnet': 'OS::Neutron::Subnet',
        'port': 'OS::Neutron::Port',
        'fip': 'OS::Neutron::FloatingIP',
        'server': 'OS::Nova::Server'
    }

    def __init__(self, name, type=None, prop=None, metadata=None, depends_on=None):
        """Init a HOT resource"""
        self.name = name
        self.type = self.RSC_TYPE_MAP.get(type, None)
        if not self.type:
            raise HOTError('Unknown resource type: ' + type)
        self.prop = prop or {}
        # optional sections
        self.metadata = metadata
        self.depends_on = depends_on

    def get_output_dict(self):
        """Output a resource as a nested dict"""
        rsc = OrderedDict()
        rsc[self.TYPE] = self.type
        if self.prop:
            rsc[self.PROPERTIES] = self.prop

        return {self.name: rsc}


class HOT(object):

    """HOT Template Constructor

    Parameters, resources, outputs are stored in a list which preserves the order
    """

    SECTIONS = (VERSION, DESCRIPTION, PARAMETER_GROUPS, PARAMETERS,
                RESOURCES, OUTPUTS, MAPPINGS) = \
        ('heat_template_version', 'description', 'parameter_groups',
         'parameters', 'resources', 'outputs', '__undefined__')

    def __init__(self, ver='2017-02-24', desc=''):
        """Init a HOT Object
        :param ver (str): Heat template version
        :param desc (str): Description of the template
        """
        self.ver = ver
        self.desc = desc
        self.parameter_lst = []
        self.resource_lst = []
        self.output_lst = []

    @staticmethod
    def _repr_ordereddict(dumper, data):
        """Represent OrderedDict as YAML node"""
        nodes = []
        for key, value in data.items():
            node_key = dumper.represent_data(key)
            node_value = dumper.represent_data(value)
            nodes.append((node_key, node_value))
        return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', nodes)

    def output_yaml_str(self):
        """Dump all sections to a str with YAML format

        The output can be read by openstack-heatclient to create a new stack

        :rtype: string
        """
        all_output_lst = list()
        all_output_dict = OrderedDict()

        # Positional sections
        desc_str = ''.join((self.DESCRIPTION, ': ', self.desc, "\n\n"))
        ver_str = ''.join((self.VERSION, ': ', self.ver, "\n\n"))
        all_output_lst.append(ver_str)
        all_output_lst.append(desc_str)

        # Parameter section
        if self.parameter_lst:
            all_para = OrderedDict()
            for para in self.parameter_lst:
                all_para.update(para.get_output_dict())
            all_output_dict.update({self.PARAMETERS: all_para})

        # Resource section
        if self.resource_lst:
            all_rsc = OrderedDict()
            for rsc in self.resource_lst:
                all_rsc.update(rsc.get_output_dict())
            all_output_dict.update({self.RESOURCES: all_rsc})

        # Output section
        if self.output_lst:
            all_output = OrderedDict()
            for output in self.output_lst:
                all_output.update(output.get_output_dict())
            all_output_dict.update({self.OUTPUTS: all_output})

        yaml.add_representer(OrderedDict, self._repr_ordereddict)
        yaml.add_representer(dict, self._repr_ordereddict)
        yaml_string = yaml.dump(all_output_dict, default_flow_style=False)
        # Remove the ' for string values
        yaml_string = yaml_string.replace('\'', '')
        yaml_string = yaml_string.replace('\n\n', '\n')
        all_output_lst.append(yaml_string)

        return ''.join(all_output_lst)


if __name__ == "__main__":
    print('Run some tests...\n')

    # Add a parameter
    para1 = Parameter('pub_net', type='string', label='public network')
    para2 = Parameter('pvt_net_name', type='string',
                      label='private network name')

    # Add a resource
    prop = {'admin_state_up': True, 'name': '{ get_param: pvt_net_name }'}
    network = Resource('net1', type='net', prop=prop)

    hot_tpl = HOT(desc="Test HOT template")
    hot_tpl.parameter_lst.append(para1)
    hot_tpl.parameter_lst.append(para2)
    hot_tpl.resource_lst.append(network)  # resource list
    print(hot_tpl.output_yaml_str())
