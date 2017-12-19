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
import pandas as pd
from matplotlib.pyplot import cm

T_FACTOR = {
    '99-4': 4.604,
    '99.9-4': 8.610,
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
ALPHA = 0.8


def plot_udp_owd(mode='l'):
    """Plot UDP one way delay"""
    base_path = './test_result/'

    sf_num_lst = np.arange(1, 11, dtype='int32')

    # Order important, smaller ones should be plotted latter
    if mode == 'l':
        sf_method_tuple = ('lkf', )
        alloc_method_tuple = ('ns', 'fn', 'nsrd')
        ms = ('plasma', )
    elif mode == 'p':
        sf_method_tuple = ('pyf', )
        alloc_method_tuple = ('fn',)
        ms = ('viridis', )
    elif mode == 'a' or mode == 'as':
        sf_method_tuple = ('lkf', 'pyf')
        alloc_method_tuple = ('fn', )
        ms = ('plasma', 'Set3')

    cmap_lst = [cm.get_cmap(m) for m in ms]

    owd_avg_map = dict()
    owd_hwci_map = dict()
    test_round = 5
    min_num_packs = 5000
    warm_up_num = 20

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
                # Use pandas
                df = pd.read_csv(
                    csv_path, error_bad_lines=False, header=None,
                    usecols=range(0, min_num_packs)
                )
                data = df.values
                if data.shape[0] < test_round:
                    print(
                        'Number of test rounds is wrong! csv: %s, number: %d' % (
                            csv_name, data.shape[0]
                        )
                    )

                tmp_lst = [np.average(
                    x) * 1000.0 for x in data[:, warm_up_num:]]

                # Check speicial test round
                if cur_mt == 'lkf-ns' and srv_num == 7:
                    import ipdb
                    # ipdb.set_trace()

                # Check outliers
                tmp_avg = np.average(tmp_lst)
                tmp_std = np.std(tmp_lst)
                for val in tmp_lst:
                    if np.abs(val - tmp_avg) >= 2 * tmp_std:
                        print('Outliers found, csv path:%s' % csv_path)
                        import ipdb
                        ipdb.set_trace()
                # Calc avg and hwci
                owd_avg_lst.append(np.average(tmp_lst))
                owd_hwci_lst.append((T_FACTOR['99-%d' % test_round] *
                                     np.std(tmp_lst)) / np.sqrt(test_round - 1))
            # cur_mt is defined in the inner-loop
            owd_avg_map[cur_mt] = owd_avg_lst
            owd_hwci_map[cur_mt] = owd_hwci_lst

    print(owd_avg_map)
    print(owd_hwci_map)

    ##########
    #  Plot  #
    ##########

    width = 0.25
    label_map = {
        'lkf-fn': 'KF, Fill One',
        'lkf-ns': 'KF, Nova Scheduler Default',
        'lkf-nsrd': 'KF, NSD Reordered',
        'pyf-fn': 'PyF, Fill One',
        'pyf-ns': 'PyF, Nova Scheduler Default',
        'pyf-nsrd': 'PyF, NSD Reordered'
    }

    ax_lst = list()
    if mode != 'as':
        fig, ax = plt.subplots()
        ax_lst.extend([ax, ax])
    else:
        fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
        ax_lst.extend([ax1, ax2])

    for sf_idx, sf_mt in enumerate(sf_method_tuple):
        # change color map here
        for all_idx, alloc_mt in enumerate(alloc_method_tuple):
            cur_mt = '-'.join((sf_mt, alloc_mt))
            avg_lst = owd_avg_map[cur_mt]
            err_lst = owd_hwci_map[cur_mt]
            pos = 0 + all_idx * width
            x = [pos + x for x in sf_num_lst]
            ax_lst[sf_idx].bar(
                x, avg_lst, width, alpha=ALPHA,
                yerr=err_lst,
                color=cmap_lst[sf_idx](
                    float(all_idx) / len(alloc_method_tuple)),
                edgecolor=cmap_lst[sf_idx](
                    float(all_idx) / len(alloc_method_tuple)),
                label=label_map[cur_mt],
                error_kw=dict(elinewidth=1, ecolor='red')
            )
    if mode != 'as':
        ax = ax_lst[0]
        ax.set_xticks(
            sf_num_lst + (width / 2.0) * (len(alloc_method_tuple) - 1)
        )
        ax.set_xticklabels(sf_num_lst, fontsize=font_size, fontname=font_name)
        ax.set_ylabel("One-way Delay (ms)",
                      fontsize=font_size, fontname=font_name)
        ax.set_xlabel("Number of chained SFIs",
                      fontsize=font_size, fontname=font_name)

        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels, fontsize=font_size,
                  loc='upper left')

        ax.yaxis.grid(which='major', lw=0.5, ls='--')
    else:
        for ax in ax_lst:
            ax.set_xticks(
                sf_num_lst + (width / 2.0) * (len(alloc_method_tuple) - 1)
            )
            ax.set_xticklabels(
                sf_num_lst, fontsize=font_size, fontname=font_name)
            # ax.set_xlabel("Number of chained SFIs",
            # fontsize=font_size, fontname=font_name)
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles, labels, fontsize=font_size - 2,
                      loc='upper left')
            ax.yaxis.grid(which='major', lw=0.5, ls='--')
        ax = ax_lst[0]
        ax.set_ylabel("One-way Delay (ms)",
                      fontsize=font_size, fontname=font_name)
        # Add a shared x label
        fig.text(0.5, 0.04, 'Number of chained SFIs', ha='center',
                 fontsize=font_size, fontname=font_name)

    fig.savefig('one_way_delay_%s.pdf' % mode,
                bbox_inches='tight', dpi=400, format='pdf')


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError('Missing mode options. Use l, f or a')
    plot_udp_owd(sys.argv[1])
