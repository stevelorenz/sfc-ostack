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

from sfcostack import conf, sfc_mngr


def cli():
    """CLI"""
    parser = argparse.ArgumentParser(description='Desp')
    parser.add_argument("conf_path", help="configuration file path")
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(0)
    args = parser.parse_args()
    print(args)


def dev_test():
    """Run tests during developing"""
    conf_hd = conf.ConfigHolder('yaml', './conf_example.yaml')
    logger = logging.getLogger(__name__)
    logger.debug('Run tests for developing...')
    sfcmngr = sfc_mngr.SFCMngr(conf_hd)
    sfcmngr.create()
    # sfcmngr.delete()


if __name__ == "__main__":
    dev_test()
