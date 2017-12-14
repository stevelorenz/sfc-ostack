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
    '99-5': 4.032,
    '99.9-5': 6.869,
    '99-10': 3.169,
    '99.9-10': 4.587,
    '99-inf': 2.576,
    '99-15': 2.947,
    '99.9-15': 4.073
}

font_size = 9
font_name = 'monospace'
mpl.rc('font', family=font_name)


def plot_udp_owd():
    """Plot UDP one way delay"""
    base_path = './test_result/'
    warm_up_num = 20

    sf_num_lst = range(1, 11)
    # sf_method_tuple = ('lkf', 'pyf')
    sf_method_tuple = ('pyf', )
    # alloc_method_tuple = ('ns', 'fn', 'nsrd')
    alloc_method_tuple = ('fn', )
    owd_avg_map = dict()
    owd_hwci_map = dict()
    test_round = 5

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
                tmp_lst = [np.average(
                    x) * 1000.0 for x in data[:, warm_up_num:]]
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

    py_cmap = cm.get_cmap('plasma')
    width = 0.25
    label_map = {
        'pyf-fn': 'PyF, Fill One'
    }

    fig, ax = plt.subplots()

    for sf_mt in sf_method_tuple:
        # change color map here
        for alloc_mt in alloc_method_tuple:
            cur_mt = '-'.join((sf_mt, alloc_mt))
            avg_lst = owd_avg_map[cur_mt]
            err_lst = owd_hwci_map[cur_mt]
            pos = 0
            x = [pos + x for x in range(1, 11)]
            ax.bar(
                x, avg_lst, width, alpha=0.8,
                yerr=err_lst, color='blue', edgecolor='blue',
                label=label_map[cur_mt]
            )

    ax.set_ylabel("One-way Delay (ms)", fontsize=font_size, fontname=font_name)
    ax.set_xlabel("Number of chained SFIs",
                  fontsize=font_size, fontname=font_name)

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, fontsize=font_size,
              loc='upper left')

    ax.yaxis.grid(which='major', lw=0.5, ls='--')
    fig.savefig('one_way_delay.pdf',
                bbox_inches='tight', dpi=400, format='pdf')


if __name__ == "__main__":
    plot_udp_owd()
