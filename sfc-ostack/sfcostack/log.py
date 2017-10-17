#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Logging

Email: xianglinks@gmail.com
"""

import logging

logger = logging.getLogger('sfc-ostack')

LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}

FORMAT = {
    'default': '%(asctime)s %(message)s',
    'debug': '%(asctime)s %(levelname)-8s %(module)s %(lineno)d %(message)s',
    'info': '%(asctime)s %(message)s'
}


def conf_logger(level, handler=None, formatter=None):
    """Config sfc-ostack logger

    :param level (str): logging level in lowercase
    :param handler: Logging handler
    :param formatter: Logging formatter
    """
    logger.setLevel(LEVELS[level])
    if not handler:
        handler = logging.StreamHandler()
    if not formatter:
        formatter = logging.Formatter(FORMAT.get(level, FORMAT['default']))

    handler.setFormatter(formatter)
    logger.addHandler(handler)
