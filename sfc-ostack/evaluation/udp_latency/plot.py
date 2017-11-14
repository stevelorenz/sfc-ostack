#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Plot Results of Latency Measurements

Email: xianglinks@gmail.com
"""


import os
import sys

import ipdb
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt


T_FACTOR = 2.576

font_size = 9
font_name = 'Monospace'
mpl.rc('font', family=font_name)
# mpl.use('TkAgg')


def plot_single_host():

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
            lat_hwci = (T_FACTOR * lat_std) / np.sqrt(pack_num - 1)
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

        ax.bar(x + pos, y, width=width, yerr=lat_hwci_map[method],
               label=label, color=color,
               error_kw=dict(elinewidth=1, ecolor='black'))

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
            lat_hwci = (T_FACTOR * lat_std) / np.sqrt(pack_num - 1)
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
    elif sys.argv[1] == '-a':
        plot_single_host()
        plot_three_host()
        plt.show()
    else:
        raise RuntimeError('Hehe...')
