#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Plot results of UDP one-way-delay measurements

Email: xianglinks@gmail.com
"""


import os
import sys

import ipdb
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm

T_FACTOR = {
    '99-10': 3.169,
    '99.9-10': 4.587,
    '99-inf': 2.576,
    '99-15': 2.947,
    '99.9-15': 4.073
}


def plot_udp_owd():
    """Plot UDP one way delay"""
    base_path = './test_result/'
    warm_up_num = 20

    sf_num_lst = (1, 10)
    sf_method_tuple = ('lkf', 'pyf')
    # sf_method_tuple = ('pyf', )
    alloc_method_tuple = ('ns', 'fn', 'nsrd')
    owd_avg_map = dict()
    owd_hwci_map = dict()
    test_round = 15

    ##########
    #  Clac  #
    ##########

    for sf_mt in sf_method_tuple:
        for alloc_mt in alloc_method_tuple:
            cur_mt = '-'.join((sf_mt, alloc_mt))
            print(cur_mt)
            owd_avg_lst = list()
            owd_hwci_lst = list()
            for srv_num in sf_num_lst:
                csv_name = '%s-owd-%d.csv' % (cur_mt, srv_num)
                csv_path = os.path.join(base_path, csv_name)
                data = np.genfromtxt(csv_path, delimiter=',')
                if data.shape[0] != test_round:
                    raise RuntimeError(
                        'Test round is wrong! csv: %s' % csv_name)
                # Calc avg and hwci
                tmp_lst = [np.average(x) for x in data[:, warm_up_num:]]
                owd_avg_lst.append(np.average(tmp_lst))
                owd_hwci_lst.append((T_FACTOR['99.9-%d' % test_round] *
                                     np.std(tmp_lst)) / np.sqrt(test_round - 1))

        owd_avg_map[cur_mt] = owd_avg_lst
        owd_hwci_map[cur_mt] = owd_hwci_lst

    print(owd_avg_map)
    print(owd_hwci_map)

    ##########
    #  Plot  #
    ##########


if __name__ == "__main__":
    plot_udp_owd()
