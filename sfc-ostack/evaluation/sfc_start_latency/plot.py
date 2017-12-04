#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Plot results of SFC start and gap latency tests

       1. SFC start time: Time for creation of all SFC resources, which contains
       network ports, SF server instance, port chain and time for waiting all SF
       programs to be ready.

       2. SFC gap time: The time between last 'old' packet and first 'new'
       chain-processed packet.

Email: xianglinks@gmail.com
"""

import os
import sys

import ipdb
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm

# Shared font config
font_size = 9
font_name = 'monospace'
mpl.rc('font', family=font_name)

# Maximal number of SF servers in the chain
MAX_CHN_NUM = 8
TEST_ROUND = 30

x = np.arange(1, MAX_CHN_NUM + 1, 1, dtype='int32')
width = 0.5

# 99% for two sided, student distribution
T_FACTOR = {
    30: 2.750,
    40: 2.704,
    50: 2.678
}

T_FACTOR_N = {
    '99-10': 3.169,
    '99.9-10': 4.587,
    '99-inf': 2.576,
    '99-15': 2.947,
    '99.9-15': 4.073
}

cmap = cm.get_cmap('plasma')
# cmap = plt.get_cmap('hsv')


def save_fig(fig, path):
    """Save fig to path"""
    fig.savefig(path + '.pdf',
                bbox_inches='tight', dpi=400, format='pdf')


def plot_single_node():
    """Plot results on single node"""

    base_path = './test_result/single_node/'

    fig_s, ax_arr = plt.subplots(2, sharex=True)

    ax_arr[0].set_title("SFC start time", fontsize=font_size +
                        1, fontname=font_name)

    ax_arr[1].set_title("SFC gap time", fontsize=font_size +
                        1, fontname=font_name)

    total_srv_chn_time = list()
    total_port_chn_time = list()
    total_gap_time = list()

    for srv_num in range(1, MAX_CHN_NUM + 1):
        ins_ts_len = 4 + 2 * srv_num
        ctl_csv = os.path.join(base_path, 'sfc-ts-ctl-%d.csv' % srv_num)
        ctl_arr = np.genfromtxt(ctl_csv, delimiter=',')
        ctl_arr = ctl_arr[:][:TEST_ROUND]

        srv_chn_time_arr = np.subtract(ctl_arr[:, [1]], ctl_arr[:, [0]])
        port_chn_time_arr = np.subtract(ctl_arr[:, [3]], ctl_arr[:, [2]])

        total_srv_chn_time.append(
            (
                np.average(srv_chn_time_arr),
                (T_FACTOR[TEST_ROUND] * np.std(srv_chn_time_arr)) /
                np.sqrt(TEST_ROUND - 1)
            )
        )

        total_port_chn_time.append(
            (
                np.average(port_chn_time_arr),
                (T_FACTOR[TEST_ROUND] * np.std(port_chn_time_arr)) /
                np.sqrt(TEST_ROUND - 1)
            )
        )

        ins_csv = os.path.join(base_path, 'sfc-ts-ins-1-%d.csv' % srv_num)
        ins_arr = np.genfromtxt(ins_csv, delimiter=',')
        ins_arr = ins_arr[:][:TEST_ROUND]
        gap_time_arr = np.subtract(ins_arr[:, [-2]], ins_arr[:, [-1]])

        total_gap_time.append(
            (
                np.average(gap_time_arr),
                (T_FACTOR[TEST_ROUND] * np.std(gap_time_arr)) /
                np.sqrt(TEST_ROUND - 1)
            )
        )

    # Plot server chain start time
    ax_arr[0].bar(
        x + width / 2.0, [y[0] for y in total_srv_chn_time], width, alpha=0.6,
        yerr=[y[1] for y in total_srv_chn_time], color='blue', edgecolor='blue',
        error_kw=dict(elinewidth=1, ecolor='black'),
        label='Server Chain'
    )

    ax_arr[0].bar(
        x + width / 2.0, [y[0] for y in total_port_chn_time], width, alpha=0.6,
        yerr=[y[1] for y in total_port_chn_time], color='green', edgecolor='green',
        error_kw=dict(elinewidth=1, ecolor='black'),
        bottom=[y[0] for y in total_srv_chn_time],
        label='Port Chain'
    )

    # ax_arr[0].plot(x + width / 2.0, [y[0] for y in total_srv_chn_time],
    #                # marker='o', markerfacecolor='None', markeredgewidth=0.5, markeredgecolor='black',
    #                color='green', lw=0.5, ls='--')

    # Plot port chain start time

    # Plot gap time
    ax_arr[1].bar(
        x + width / 2.0, [y[0] for y in total_gap_time], width, alpha=0.6,
        yerr=[y[1] for y in total_gap_time], color='red', edgecolor='black',
        error_kw=dict(elinewidth=1, ecolor='black')
    )

    ax_arr[1].set_xticks(x + width / 2.0)
    ax_arr[1].set_xticklabels(x, fontsize=font_size, fontname=font_name)
    ax_arr[1].set_xlim(0.5, 9)
    ax_arr[1].set_xlabel("Number of chained SF-server(s)",
                         fontsize=font_size, fontname=font_name)

    for ax in ax_arr:
        ax.set_ylabel("Second", fontsize=font_size, fontname=font_name)

    # Add legend for all axis
    for ax in (ax_arr[0], ):
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels, fontsize=font_size,
                  loc='best')

        # ax.grid()

    # fig_s.savefig('./sfc_start_time.png', dpi=500, bbox_inches='tight')
    fig_s.savefig('./sfc_start_time.png', dpi=500)


def plot_start_three_compute(inc_wait=True):
    """Plot results on three compute nodes"""

    test_round = 10

    ##########
    #  Calc  #
    ##########

    min_sf_num = 1
    max_sf_num = 10

    result_map = dict()  # key is method

    method_tuple = ('ns', 'fn', 'nsrd')
    ts_info_tuple = (
        'Server instances launch time',
        'Waiting time for SF program',
        'Chain reordering time',
        'Port Chain building time'
    )
    if not inc_wait:
        ts_info_tuple = (
            'Server instances launch time',
            'Chain reordering time',
            'Port Chain building time'
        )

    base_path = './test_result/three_compute/'

    for method in method_tuple:
        srv_num_result = list()
        for srv_num in range(min_sf_num, max_sf_num + 1):
            ctl_fn = '%s-sfc-ts-ctl-%d.csv' % (method, srv_num)
            ctl_csvp = os.path.join(base_path, ctl_fn)
            ctl_data = np.genfromtxt(ctl_csvp, delimiter=',')
            if ctl_data.shape[0] != test_round:
                raise RuntimeError(
                    'Number of test rounds is wrong, path: %s' % ctl_csvp
                )
            if not inc_wait:
                srv_num_result.append(
                    [np.average(ctl_data[:, x]) for x in (0, 2, 3)]
                )
            else:
                srv_num_result.append(
                    [np.average(ctl_data[:, x]) for x in range(0, 4)]
                )

        result_map[method] = srv_num_result

    ##########
    #  Plot  #
    ##########

    method_label_tuple = ('NSD', 'FO', 'NSDRO')

    fig, ax = plt.subplots()
    width = 0.25

    hatch_typ = ['/', '+', 'X']

    # MARK: I don't know hot to plot this better...
    for m_idx, method in enumerate(method_tuple):
        pos = 0 + m_idx * width
        result_lst = result_map[method]

        colors = [cmap(x * 1 / len(ts_info_tuple))
                  for x in range(len(ts_info_tuple))]

        # TODO: should be plot with list
        for srv_num, ts_tuple in enumerate(result_lst):
            for t_idx, ts in enumerate(ts_tuple):
                ax.bar(
                    srv_num + 1 + pos, ts_tuple[t_idx], width, alpha=0.6,
                    bottom=sum(ts_tuple[0:t_idx]),
                    color=colors[t_idx], edgecolor=colors[t_idx],
                    label=method_label_tuple[m_idx] +
                    ", " + ts_info_tuple[t_idx],
                    # hatch=hatch_typ[m_idx]
                )

    save_fig(fig, './sfc_start_time')
    fig.show()


def plot_gap_three_compute():

    ##########
    #  Calc  #
    ##########

    min_sf_num = 1
    max_sf_num = 10

    result_map = dict()
    test_round = 10
    method_tuple = ('ns', 'fn', 'nsrd')
    base_path = './test_result/three_compute/'

    for method in method_tuple:
        srv_num_result = list()
        for srv_num in range(min_sf_num, max_sf_num + 1):
            ins_fn = '%s-sfc-ts-ins-%d.csv' % (method, srv_num)
            ins_csvp = os.path.join(base_path, ins_fn)
            ins_data = np.genfromtxt(ins_csvp, delimiter=',')
            if ins_data.shape[0] != test_round:
                raise RuntimeError(
                    'Number of test rounds is wrong, path: %s' % ins_csvp
                )
            else:
                srv_num_result.append(
                    np.average(np.subtract(ins_data[:, -2], ins_data[:, -1]))
                )

        result_map[method] = srv_num_result

    ##########
    #  Plot  #
    ##########

    method_label_tuple = ('NSD', 'FO', 'NSDRO')

    fig, ax = plt.subplots()
    width = 0.25

    colors = [cmap(x * 1 / len(method_tuple)) for x in range(len(method_tuple))]

    for m_idx, method in enumerate(method_tuple):
        gt_lst = result_map[method]
        pos = 0 + m_idx * width
        x = [pos + x for x in range(min_sf_num, max_sf_num + 1)]
        ax.bar(
            x, gt_lst, width, alpha=0.6,
            color=colors[m_idx], edgecolor=colors[m_idx],
            label=method_label_tuple[m_idx]
        )

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, fontsize=font_size - 2,
              loc='best')
    ax.grid(linestyle='--', lw=0.5)

    save_fig(fig, './sfc_gap_time')
    fig.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError('Missing options.')
    if sys.argv[1] == '-s':
        plot_single_node()
        plt.show()
    elif sys.argv[1] == '-msw':
        plot_start_three_compute(inc_wait=True)
        plt.show()
    elif sys.argv[1] == '-msnw':
        plot_start_three_compute(inc_wait=False)
        plt.show()
    elif sys.argv[1] == '-mg':
        plot_gap_three_compute()
        plt.show()
    else:
        raise RuntimeError('Hehe...')
