#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Command-Line Tool
Email: xianglinks@gmail.com
"""

import argparse
import logging
import sys
sys.path.insert(0, '../')

from sfcostack import conf
from sfcostack.resource import sfc_rsc


def cli():
    """CLI Entry"""
    logger = logging.getLogger(__name__)
    desc = 'SFC-OSTACK Framework'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument(
        'conf_path', help='Path of configuration file(YAML format).', type=str
    )
    parser.add_argument(
        'operation', help='Operation for SFC', choices=['create', 'delete']
    )

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(0)
    args = parser.parse_args()

    conf_hd = conf.ConfigHolder('yaml', args.conf_path)
    sfc = sfc_rsc.SFC(conf_hd)

    if args.operation == 'create':
        logger.info('Create the SFC, config file path: %s' % args.conf_path)
        sfc.create()
    elif args.operation == 'delete':
        logger.info('Delete the SFC, config file: %s' % args.conf_path)
        sfc.delete()


def dev_test():
    """Run tests during developing"""
    conf_hd = conf.ConfigHolder('yaml', './conf_example.yaml')
    logger = logging.getLogger(__name__)
    logger.info('Run tests for developing...')

    sfc = sfc_rsc.SFC(conf_hd)
    sfc.create()
    # sfc.delete()


if __name__ == "__main__":
    cli()
