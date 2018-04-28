#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Plot results of UDP one-way-delay measurements

Email: xianglinks@gmail.com
"""


import os
import sys
sys.path.append('../../scripts')
import tex

import ipdb
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.pyplot import cm
from scipy import stats

font_size = 9
font_name = 'monospace'
mpl.rc('font', family=font_name)
ALPHA = 0.8
cfd_level = 0.99

WARM_UP_NUM = 500


def plot_ipd_owd():
    """Plot inter-packet delay tests for owd"""
    base_path = './test_result/'
    sf_method_tuple = ('lkf', )
    alloc_method_tuple = ('ns', )
    ipd_tuple = (0.003, 0.004, 0.005, 0.010, 0.020)
    sf_num_lst = ('10', )
    owd_avg_map = dict()
    owd_hwci_map = dict()
    cmap = cm.get_cmap('plasma')

    for sfm in sf_method_tuple:
        for alloc in alloc_method_tuple:
            for num in sf_num_lst:
                cur_typ = sfm + '-' + alloc + '-' + num
                owd_avg, owd_hwci = [], []
                for ipd in ipd_tuple:
                    csv_name = '%s-%s-%.3f-owd-%s.csv' % (sfm, alloc, ipd, num)
                    csv_path = os.path.join(base_path, csv_name)
                    # Use pandas
                    df = pd.read_csv(
                        csv_path, error_bad_lines=False, header=None,
                        usecols=range(0, 5000)
                    )
                    data = df.values
                    test_round = data.shape[0]
                    if test_round < 15:
                        print('[Warn] Not enough test round, number: %d' %
                              test_round)
                    tmp_lst = [np.average(
                        x) * 1000.0 for x in data[:, WARM_UP_NUM:]]
                    tmp_lst = tmp_lst[:15]
                    owd_avg.append(np.average(tmp_lst))
                    owd_hwci.append(
                        # Get T factor with confidence level
                        (stats.t.interval(cfd_level, test_round, loc=0, scale=1)
                         [1] * np.std(tmp_lst)) / np.sqrt(test_round - 1)
                    )
                owd_avg_map[cur_typ] = owd_avg
                owd_hwci_map[cur_typ] = owd_hwci

    print(owd_avg_map)

    ##########
    #  Plot  #
    ##########

    label_map = {
        'lkf-ns-10': 'LKF, NSD, SF_NUM = 10',
    }

    fig, ax = plt.subplots()

    sn = 0
    for cur_typ, ipd_lst in owd_avg_map.items():
        print('Current type: %s' % cur_typ)
        color = cmap(sn / float(len(owd_avg_map.keys())))
        ipd_err = owd_hwci_map[cur_typ]
        ax.errorbar(ipd_tuple, ipd_lst, yerr=ipd_err, color=color, ls='--',
                    marker='o', markerfacecolor='None', markeredgewidth=1, markeredgecolor=color,
                    label=label_map[cur_typ])
        sn += 1

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, fontsize=font_size,
              loc='upper left')

    # ax.set_xlim(0.002, 0.025)
    ax.set_xticks(ipd_tuple)
    ax.set_xticklabels([int(ipd * 1000) for ipd in ipd_tuple],
                       fontsize=font_size, fontname=font_name)
    ax.set_ylabel("One-way Delay (ms)",
                  fontsize=font_size, fontname=font_name)
    ax.set_xlabel("Inter-packet Delay (ms)",
                  fontsize=font_size, fontname=font_name)

    ax.xaxis.grid(which='major', lw=0.5, ls='--')
    ax.yaxis.grid(which='major', lw=0.5, ls='--')

    fig.savefig('one_way_delay_ipd.pdf', bbox_inches='tight',
                dpi=400, format='pdf')


def plot_plsize_owd():
    """Plot payload size tests for owd"""
    pass


def plot_udp_owd(mode='l'):
    """Plot UDP one way delay"""
    base_path = './test_result/'

    sf_num_lst = np.arange(1, 11, dtype='int32')

    # Order important, smaller ones should be plotted latter
    if mode == 'l':
        sf_method_tuple = ('lkf', )
        alloc_method_tuple = ('ns', 'fn', 'nsrd')
        ms = ('tab10', )
    elif mode == 'p':
        sf_method_tuple = ('pyf', )
        alloc_method_tuple = ('ns', 'fn', 'nsrd')
        ms = ('Set1', )
    elif mode == 'a' or mode == 'as':
        sf_method_tuple = ('lkf', 'pyf')
        alloc_method_tuple = ('ns', 'fn', 'nsrd')
        # ms = ('plasma', 'Set3')
        ms = ('tab10', 'Set1')

    cmap_lst = [cm.get_cmap(m) for m in ms]

    owd_avg_map = dict()
    owd_hwci_map = dict()
    test_round = 15
    min_num_packs = 5000
    warm_up_num = 500

    ##########
    #  Clac  #
    ##########

    for sf_mt in sf_method_tuple:
        for alloc_mt in alloc_method_tuple:
            cur_mt = '-'.join((sf_mt, alloc_mt))
            print(cur_mt + '\n' + '-' * 30)
            owd_avg_lst = list()
            owd_hwci_lst = list()
            for srv_num in sf_num_lst:
                print('--- srv_num: %d' % srv_num)
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
                tmp_lst = tmp_lst[:test_round]

                # Filter out Nan
                nan_idx = list()
                isnan_result = np.isnan(tmp_lst)
                for idx, rst in enumerate(tmp_lst):
                    if rst == True:
                        nan_idx.append(idx)
                if nan_idx:
                    print('Nan detected, nan index:')
                    print(nan_idx)

                tmp_lst = [value for value in tmp_lst if not np.isnan(value)]
                if len(tmp_lst) != test_round:
                    print('Nan detected, after filter: %d' % len(tmp_lst))

                # Check speicial test round
                if cur_mt == 'pyf-fn' and srv_num == 9:
                    # import ipdb
                    # ipdb.set_trace()
                    pass

                # Check outliers
                tmp_avg = np.average(tmp_lst)
                tmp_std = np.std(tmp_lst)
                ol_idx = list()
                for idx, val in enumerate(tmp_lst):
                    if np.abs(val - tmp_avg) >= 2 * tmp_std:
                        print('Outliers found, csv path:%s, index: %d' %
                              (csv_path, idx))
                        ol_idx.append(idx)
                print('Outlier list: %s' % ','.join(map(str, ol_idx)))
                # Calc avg and hwci
                owd_avg_lst.append(np.average(tmp_lst))
                # owd_hwci_lst.append((T_FACTOR['99-%d' % test_round] *
                # np.std(tmp_lst)) / np.sqrt(test_round - 1))
                owd_hwci_lst.append(
                    # Get T factor with confidence level
                    (stats.t.interval(cfd_level, test_round, loc=0, scale=1)
                     [1] * np.std(tmp_lst)) / np.sqrt(test_round - 1)
                )
            # cur_mt is defined in the inner-loop
            owd_avg_map[cur_mt] = owd_avg_lst
            owd_hwci_map[cur_mt] = owd_hwci_lst

    # print(owd_avg_map)
    # print(owd_hwci_map)

    ##########
    #  Plot  #
    ##########

    tex.setup(width=1, height=None, span=False, l=0.15, r=0.98, t=0.98, b=0.17,
              params={})

    width = 0.25
    label_map = {
        'lkf-fn': 'LKF LC',
        'lkf-ns': 'LKF LB',
        'lkf-nsrd': 'LKF LBLC',
        'pyf-fn': 'PyF LC',
        'pyf-ns': 'PyF LB',
        'pyf-nsrd': 'PyF LBLC'
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
                color=cmap_lst[sf_idx](all_idx),
                edgecolor=cmap_lst[sf_idx](all_idx),
                label=label_map[cur_mt],
                error_kw=dict(elinewidth=1, ecolor='red')
            )
    if mode != 'as':
        ax = ax_lst[0]
        ax.set_xticks(
            sf_num_lst + (width / 2.0) * (len(alloc_method_tuple) - 1)
        )
        ax.set_xticklabels(sf_num_lst)
        ax.set_ylabel("OWD (ms)")
        ax.set_xlabel("Chain length")
        ax.set_ylim(0, 11)

        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels, loc='upper left')

        ax.yaxis.grid(which='major', lw=0.5, ls='--')
    else:
        for ax in ax_lst:
            ax.set_xticks(
                sf_num_lst + (width / 2.0) * (len(alloc_method_tuple) - 1)
            )
            ax.set_xticklabels(sf_num_lst)
            # ax.set_xlabel("Number of chained SFIs",
            # fontsize=font_size, fontname=font_name)
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles, labels, loc='upper left')
            ax.yaxis.grid(which='major', lw=0.5, ls='--')
        ax = ax_lst[0]
        ax.set_ylabel("OWD (ms)",
                      fontsize=font_size, fontname=font_name)
        # Add a shared x label
        fig.text(0.5, 0.04, 'Chain length', ha='center',
                 fontsize=font_size, fontname=font_name)

    fig.savefig('one_way_delay_%s.pdf' % mode, pad_inches=0,
                bbox_inches='tight', dpi=400, format='pdf')


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError('Missing mode options. Use l, f or a')
    elif sys.argv[1] == 'ipd':
        plot_ipd_owd()
    elif sys.argv[1] == 'pls':
        plot_plsize_owd()
    else:
        plot_udp_owd(sys.argv[1])
