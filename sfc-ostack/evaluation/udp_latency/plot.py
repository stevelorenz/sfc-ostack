#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Plot Results of Latency Measurements
       Lesson learned here: Should learn and use pandas...

Email: xianglinks@gmail.com
"""


import os
import sys

import ipdb
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm

T_FACTOR_INF = 2.576
T_FACTOR_TEN = 3.169

T_FACTOR = {
    '99-10': 3.169,
    '99.9-10': 4.587,
    '99-inf': 2.576
}

font_size = 9
font_name = 'Monospace'
mpl.rc('font', family=font_name)
# mpl.use('TkAgg')

cmap = cm.get_cmap('plasma')


def warn_three_std(value_lst):
    """Raise exception if the value is not in the three std +- mean value of
    value_lst
    """
    avg = np.average(value_lst)
    std = np.std(value_lst)

    for value in value_lst:
        if abs(value - avg) >= 3.0 * std:
            error_msg = 'Value %s is not located in three std range of list: %s' % (
                value, ', '.join(map(str, value_lst)))


def plot_ipd():
    """Plot tests for inter-packet delay"""

    base_path = './test_result/three_compute/ipd/'
    payload_len = 512
    test_round = 10
    # test_round = 9

    lat_avg_map = dict()
    lat_hwci_map = dict()

    ##########
    #  Calc  #
    ##########

    for sf_num in (0, 1, 10):
        lat_avg_lst = []
        lat_hwci_lst = []
        for ipd in (3, 4, 5, 10, 20):
            send_rate = int(np.ceil(payload_len / (ipd / 1000.0)))

            cur_rd_avg_lst = list()
            # Loop for all test rounds
            for rd in range(1, test_round + 1):
                csv_path = os.path.join(base_path, 'ipd-ns-%s-512-%s-%s.csv'
                                        % (send_rate, sf_num, rd))
                cur_lat_arr = np.genfromtxt(csv_path, delimiter=',')[
                    # MARK: Filter first 10 init packets.
                    10:, 1] / 1000.0
                cur_rd_avg_lst.append(np.average(cur_lat_arr))

            lat_avg_lst.append(np.average(cur_rd_avg_lst))
            lat_hwci_lst.append(
                (T_FACTOR['99.9-10'] * np.std(cur_rd_avg_lst)) /
                np.sqrt(test_round - 1)
            )

        warn_three_std(lat_avg_lst)
        lat_avg_map[sf_num] = lat_avg_lst
        lat_hwci_map[sf_num] = lat_hwci_lst

    print('Avg:')
    for sf_num, lat_lst in lat_avg_map.items():
        print('SF number: %d' % sf_num)
        print(lat_lst)

    print('HWCI:')
    for sf_num, lat_lst in lat_hwci_map.items():
        print('SF number: %d' % sf_num)
        print(lat_lst)

    ##########
    #  Plot  #
    ##########

    fig, ax = plt.subplots()

    x = (3, 4, 5, 10, 20)

    sf_num_lst = (0, 1, 10)

    colors = [cmap(x * 1 / len(sf_num_lst)) for x in range(len(sf_num_lst))]

    for method in ('KF', ):
        label_gen = (
            method + ', ' + appendix for appendix in ('SF_NUM = 0', 'SF_NUM = 1',
                                                      'SF_NUM = 10'))
        for sf_num, color, label in zip(
            (0, 1, 10), colors,
            label_gen,
        ):
            y = lat_avg_map[sf_num]
            ax.errorbar(x, y, yerr=lat_hwci_map[sf_num], color=color, label=label,
                        marker='o', markerfacecolor='None', markeredgewidth=1, markeredgecolor=color,
                        linestyle='--'
                        )

    ax.set_xlabel("Inter-packet Delay (ms)",
                  fontsize=font_size, fontname=font_name)

    ax.axvline(x=4, ymin=0, ymax=14, ls='--', lw=0.4, color='black')

    # ax.bar(x=4, height=8, bottom=2, width=0.5, color='white', ls='--', lw=1,
    #       edgecolor='black'
    #       )
    ax.set_xticks((2, 3, 4, 5, 10, 20))
    # ax.set_xticks(x + width / 2.0)
    # ax.set_xticklabels(x, fontsize=font_size, fontname=font_name)
    # ax.set_xlim(0, 20)
    # ax.set_yticks(range(0, 7))
    # ax.set_yticklabels(range(0, 7), fontsize=font_size, fontname=font_name)
    ax.set_ylabel("RTT (ms)", fontsize=font_size, fontname=font_name)
    ax.set_ylim(0, 14)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, fontsize=font_size - 1,
              loc='upper right')
    ax.grid(linestyle='--', lw=0.5)

    fig.show()
    fig.savefig('./ipd_three_compute_full.png', dpi=400, format='png')


def plot_plen():
    """Plot tests for UDP payload length"""

    base_path = './test_result/three_compute/plen/'
    ipd = 4
    test_round = 10
    sf_num_lst = (0, 1, 10)

    plen_lst = [2**x * 128 for x in range(0, 5)]
    print('Payload list: ' + ','.join(map(str, plen_lst)))
    # sys.exit(1)

    ##########
    #  Calc  #
    ##########

    lat_avg_plen = list()
    lat_hwci_plen = list()

    for sf_num in sf_num_lst:
        lat_avg_lst = []
        lat_hwci_lst = []
        for plen in plen_lst:
            send_rate = int(np.ceil(plen / (ipd / 1000.0)))
            cur_rd_avg_lst = list()
            for rd in range(1, test_round + 1):
                csv_path = os.path.join(base_path, 'plen-ns-%s-%s-%s-%s.csv'
                                        % (send_rate, plen, sf_num, rd))
                cur_lat_arr = np.genfromtxt(csv_path, delimiter=',')[
                    # MARK: Filter first 10 init packets.
                    10:, 1] / 1000.0
                cur_rd_avg_lst.append(np.average(cur_lat_arr))

            lat_avg_lst.append(np.average(cur_rd_avg_lst))
            lat_hwci_lst.append(
                (T_FACTOR['99.9-10'] * np.std(cur_rd_avg_lst)) /
                np.sqrt(test_round - 1)
            )

        warn_three_std(lat_avg_lst)
        lat_avg_plen.append(lat_avg_lst)
        lat_hwci_plen.append(lat_hwci_lst)

    print('Avg:')
    for idx, lat_lst in enumerate(lat_avg_plen):
        print('Index number: %d' % idx)
        print(lat_lst)

    print('HWCI:')
    for idx, lat_lst in enumerate(lat_hwci_plen):
        print('Index number: %d' % idx)
        print(lat_lst)

    ##########
    #  Plot  #
    ##########

    fig, ax = plt.subplots()

    width = 0.3

    suffix = ['SF_NUM = %s' % sf for sf in sf_num_lst]
    colors = [cmap(x * 1 / len(sf_num_lst)) for x in range(len(sf_num_lst))]

    for mt_idx, method in enumerate(['KF']):
        label_gen = (
            method + ', ' + suf for suf in suffix)

        for sf_idx, label, color in zip((0, 1, 2), label_gen,
                                        # ('green', 'blue', 'red')):
                                        colors):
            pos = [0 + sf_idx * width] * len(plen_lst)
            cur_x = [sf_idx * width + x for x in range(1, 6)]
            ax.bar(cur_x, lat_avg_plen[sf_idx], yerr=lat_hwci_plen[sf_idx],
                   error_kw=dict(elinewidth=1, ecolor='black'),
                   width=width, color=color, lw=1, label=label)

    ax.set_xticks([x + (len(sf_num_lst) - 1) *
                   width / 2.0 for x in range(1, 6)])
    ax.set_xticklabels(plen_lst, fontsize=font_size, fontname=font_name)
    ax.set_xlabel('UDP Payload Length (bytes)')
    # ax.set_xlim(0, 20)
    # ax.set_yticks(range(0, 7))
    # ax.set_yticklabels(range(0, 7), fontsize=font_size, fontname=font_name)
    ax.set_ylabel("RTT (ms)", fontsize=font_size, fontname=font_name)
    ax.set_ylim(0, 14)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, fontsize=font_size - 1,
              loc='upper right')
    ax.grid(linestyle='--', lw=0.5)

    fig.show()
    fig.savefig('./plen_three_compute_full.png', dpi=400, format='png')


def plot_single_host():
    """Plot UDP RTT tests on single host"""

    base_path = './test_result/single_node/'

    send_rate = 1000  # byte/s
    payload_len = 512  # byte
    num_packets = 10000

    min_fs_num = 0
    max_fs_num = 10

    method_tuple = ('lkf', 'pyf')

    ##########
    #  Calc  #
    ##########

    lat_avg_map = dict()
    lat_hwci_map = dict()

    lat_avg_diff_map = dict()

    for method in method_tuple:
        base_file_name = '-'.join(
            map(str, (method, num_packets, send_rate, payload_len))
        )

        lat_avg_tmp = []
        lat_hwci_tmp = []

        for srv_num in range(min_fs_num, max_fs_num + 1):
            csv_path = os.path.join(base_path,
                                    base_file_name + '-%d.csv' % srv_num)
            data = np.genfromtxt(csv_path, delimiter=',')
            pack_num = data.shape[0]
            lat_data = data[1:, 1] / 1000.0
            lat_avg = np.average(lat_data)
            lat_avg_tmp.append(lat_avg)
            lat_std = np.std(lat_data)
            lat_hwci = (T_FACTOR_INF * lat_std) / np.sqrt(pack_num - 1)
            lat_hwci_tmp.append(lat_hwci)

        lat_avg_map[method] = lat_avg_tmp
        lat_hwci_map[method] = lat_hwci_tmp

        # print('SF num:%d, avg:%f, std:%f, hwci:%f'
        # % (srv_num, lat_avg, lat_std, lat_hwci))

    for method in method_tuple:
        diff_lst = list()
        avg_lst = lat_avg_map[method]
        last = avg_lst[1]
        for lat in avg_lst[2:]:
            diff_lst.append(lat - last)
            last = lat
        lat_avg_diff_map[method] = diff_lst

    for method in method_tuple:
        print('Method: %s' % method)
        print(lat_avg_map[method])
        print(lat_hwci_map[method])
        print(lat_avg_diff_map[method])

    ##########
    #  Plot  #
    ##########

    # ------ Plot Abs -------

    fig, ax = plt.subplots()

    # ax.set_title("Service Function: IP Forwarding", fontsize=font_size + 1,
    # # fig.suptitle('Latency(RTT) for UDP Packets', fontsize=13)
    # fontname=font_name)

    x = np.arange(min_fs_num, max_fs_num + 1, 1, dtype='int32')
    width = 0.4

    for method, color, label, pos in zip(
        method_tuple, ('blue', 'green'),
        ('Kernel forwarding', 'Python forwarding'),
        (0, width)
    ):
        y = lat_avg_map[method]

        ax.plot(x + pos, y,
                # marker='o', markerfacecolor='None', markeredgewidth=1, markeredgecolor=color,
                color=color, lw=1, ls='--')

        # ax.bar(x + pos, y, width=width,
        #        label=label, color=color)

        ax.bar(x + pos, y, width=width,
               label=label, color=color)

    ax.set_xlabel("Number of chained SF-servers",
                  fontsize=font_size, fontname=font_name)
    ax.set_xticks(x + width / 2.0)
    ax.set_xticklabels(x, fontsize=font_size, fontname=font_name)
    # ax.set_xlim(0 - (width * 2), 11)
    ax.set_yticks(range(0, 7))
    ax.set_yticklabels(range(0, 7), fontsize=font_size, fontname=font_name)
    ax.set_ylabel("RTT (ms)", fontsize=font_size, fontname=font_name)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, fontsize=font_size,
              loc='upper left')
    ax.grid(linestyle='--', lw=0.5)

    fig.show()
    fig.savefig('./udp_rtt_single_host.png', dpi=400, format='png')

    # --- Plot the abs difference ---

    fig1, ax1 = plt.subplots()

    x = np.arange(min_fs_num + 2, max_fs_num + 1, 1, dtype='int32')
    width = 0.4

    for method, color, label, pos in zip(
        ('lkf', 'pyf'), ('blue', 'green'),
        ('Kernel forwarding', 'Python forwarding'),
        (0, width)
    ):
        y = lat_avg_diff_map[method]

        ax1.plot(x + pos, y, label=label,
                 marker='o', markerfacecolor='None', markeredgewidth=1, markeredgecolor=color,
                 color=color, lw=1, ls='--')

        # ax1.bar(x + pos, y, width=width,
        # label=label, color=color)

    ax1.set_xlabel("Number of chained SF-servers",
                   fontsize=font_size, fontname=font_name)
    ax1.set_xticks(x + width / 2.0)
    ax1.set_xticklabels(x, fontsize=font_size, fontname=font_name)
    # ax1.set_xlim(0 - (width * 2), 11)
    # ax1.set_yticks(range(0, 7))
    # ax1.set_yticklabels(range(0, 7), fontsize=font_size, fontname=font_name)
    ax1.set_ylabel("Difference (ms)", fontsize=font_size, fontname=font_name)
    ax1.set_ylim(0, 1)
    handles, labels = ax1.get_legend_handles_labels()
    ax1.legend(handles, labels, fontsize=font_size,
               loc='upper left')
    ax1.grid(linestyle='--', lw=0.5)

    fig1.show()
    fig1.savefig('./udp_reldiff_single_host.png', dpi=400, format='png')


def plot_three_host():
    """Plot UDP RTT tests on three compute hosts"""

    base_path = './test_result/three_compute/'
    send_rate = 2048  # byte/s
    payload_len = 512  # byte

    min_fs_num = 0
    max_fs_num = 10

    fig, ax = plt.subplots()

    # ax.set_title("Service Function: IP Forwarding", fontsize=font_size + 1,
    # fontname=font_name)

    x = np.arange(min_fs_num, max_fs_num + 1, 1, dtype='int32')
    width = 0.35

    method_tuple = ('lkf-fd', 'lkf-ns')

    ##########
    #  Calc  #
    ##########

    lat_avg_map = dict()
    lat_hwci_map = dict()

    lat_avg_diff_map = dict()

    for method in method_tuple:
        base_file_name = '-'.join(
            map(str, (method, send_rate, payload_len))
        )

        lat_avg_tmp = []
        lat_hwci_tmp = []

        for srv_num in range(min_fs_num, max_fs_num + 1):
            csv_path = os.path.join(base_path,
                                    base_file_name + '-%d.csv' % srv_num)
            data = np.genfromtxt(csv_path, delimiter=',')
            pack_num = data.shape[0]
            lat_data = data[:, 1] / 1000.0
            lat_avg = np.average(lat_data)
            lat_avg_tmp.append(lat_avg)
            lat_std = np.std(lat_data)
            lat_hwci = (T_FACTOR_INF * lat_std) / np.sqrt(pack_num - 1)
            lat_hwci_tmp.append(lat_hwci)

        lat_avg_map[method] = lat_avg_tmp
        lat_hwci_map[method] = lat_hwci_tmp

        # print('SF num:%d, avg:%f, std:%f, hwci:%f'
        # % (srv_num, lat_avg, lat_std, lat_hwci))

    for method in method_tuple:
        diff_lst = list()
        avg_lst = lat_avg_map[method]
        last = avg_lst[1]
        for lat in avg_lst[2:]:
            diff_lst.append(lat - last)
            last = lat
        lat_avg_diff_map[method] = diff_lst

    for method in method_tuple:
        print('Method: %s' % method)
        print(lat_avg_map[method])
        print(lat_hwci_map[method])
        print(lat_avg_diff_map[method])

    ##########
    #  Plot  #
    ##########

    # ------ Plot Abs -------

    for method, color, label, pos in zip(
        method_tuple,
        ('blue', 'green'),
        ('Kernel forwarding, fill nearst',
         'Kernel forwarding, nova scheduler'),
        (0, width)
    ):

        y = lat_avg_map[method]

        # ax.plot(x + pos + width / 2, y,
        # marker='o', markerfacecolor='None', markeredgewidth=1,
        # markeredgecolor=color, color=color, lw=1, ls='--')

        ax.bar(x + pos, y, width=width, yerr=lat_hwci_map[method],
               label=label, color=color,
               error_kw=dict(elinewidth=1, ecolor='black'))

    ax.set_xlabel("Number of chained SF-servers",
                  fontsize=font_size, fontname=font_name)
    ax.set_xticks(x + width / 2.0)
    ax.set_xticklabels(x, fontsize=font_size, fontname=font_name)
    # ax.set_yticks(range(0, 7))
    # ax.set_yticklabels(range(0, 7), fontsize=font_size, fontname=font_name)
    ax.set_ylim(6, 12)
    ax.set_ylabel("RTT (ms)", fontsize=font_size, fontname=font_name)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, fontsize=font_size - 2,
              loc='upper left')
    ax.grid(linestyle='--', lw=0.5)

    fig.savefig('./udp_rtt_three_host.png', dpi=400, format='png')
    fig.show()

    # --- Plot the abs difference ---

    fig1, ax1 = plt.subplots()

    x = np.arange(min_fs_num + 2, max_fs_num + 1, 1, dtype='int32')
    width = 0.4

    for method, color, label, pos in zip(
        method_tuple, ('blue', 'green'),
        ('Kernel forwarding', 'Python forwarding'),
        (0, width)
    ):
        y = lat_avg_diff_map[method]

        ax1.plot(x + pos, y, label=label,
                 marker='o', markerfacecolor='None', markeredgewidth=1, markeredgecolor=color,
                 color=color, lw=1, ls='--')

        # ax1.bar(x + pos, y, width=width,
        # label=label, color=color)

    ax1.set_xlabel("Number of chained SF-servers",
                   fontsize=font_size, fontname=font_name)
    ax1.set_xticks(x + width / 2.0)
    ax1.set_xticklabels(x, fontsize=font_size, fontname=font_name)
    # ax1.set_xlim(0 - (width * 2), 11)
    # ax1.set_yticks(range(0, 7))
    # ax1.set_yticklabels(range(0, 7), fontsize=font_size, fontname=font_name)
    ax1.set_ylabel("Difference (ms)", fontsize=font_size, fontname=font_name)
    # ax1.set_ylim(0, 1)
    handles, labels = ax1.get_legend_handles_labels()
    ax1.legend(handles, labels, fontsize=font_size,
               loc='upper left')
    ax1.grid(linestyle='--', lw=0.5)

    fig1.show()
    fig1.savefig('./udp_reldiff_three_host.png', dpi=400, format='png')


if __name__ == "__main__":
    if sys.argv[1] == '-s':
        plot_single_host()
        plt.show()
    elif sys.argv[1] == '-m':
        plot_three_host()
        plt.show()
    elif sys.argv[1] == '-i':
        plot_ipd()
        plt.show()
    elif sys.argv[1] == '-p':
        plot_plen()
        plt.show()
    elif sys.argv[1] == '-a':
        plot_single_host()
        plot_three_host()
        plt.show()
    else:
        raise RuntimeError('Hehe...')
