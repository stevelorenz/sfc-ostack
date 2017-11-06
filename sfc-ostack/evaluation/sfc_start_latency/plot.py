#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Plot results of SFC start latency tests

       1. SFC start time: Time for creation of all SFC resources, which contains
       network ports, SF server instance, port chain and time for waiting all SF
       programs to be ready.

       2. SFC gap time: The time between last 'old' packet and first 'new'
       chain-processed packet.

Email: xianglinks@gmail.com
"""

import os

import ipdb
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt

# Shared font config
font_size = 8
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

cmap = plt.get_cmap('hsv')

#################
#  Single Node  #
#################

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

# ipdb.set_trace()
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
