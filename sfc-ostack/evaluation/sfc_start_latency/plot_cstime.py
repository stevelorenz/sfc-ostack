#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Plot results of SFC start latency tests

Email: xianglinks@gmail.com
"""

import os

import ipdb
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt

font_size = 8
# Match the latex template
font_name = 'monospace'
mpl.rc('font', family=font_name)

MAX_FS_NUM = 2
x = np.arange(1, MAX_FS_NUM + 1, 1, dtype='int32')
width = 0.6

T_FACTOR = 2.678  # 99% for two sided, student distribution

cmap = plt.get_cmap('hsv')

# For single node
fig_s, ax_s = plt.subplots()
ax_s.set_title("Service Function: IP Forwarding", fontsize=font_size + 1,
               fontname=font_name)

BASE_PATH = './test_result/single_node/'

# To be calculated and plotted parameter
# 1. SFC start time(delay)
#   1.1 Service chain creation time
#   1.1 Service function creation time
#   1.2 Port chain creation time

# 2. SFC start gap delay
#    gap = first_b_pack - last_a_pack

############
#  Mode 0  #
############

tl_sfc_dl_lst = list()
tl_sc_dl_lst = list()
tl_pc_dl_lst = list()
tl_gap_lst = list()

for srv_num in range(1, MAX_FS_NUM + 1):
    ts_len = 3 + 2 * srv_num
    sfc_dl_lst = list()
    sc_dl_lst = list()
    pc_dl_lst = list()
    gap_lst = list()

    # ipdb.set_trace()
    ctl_csv = os.path.join(BASE_PATH, 'sfc-ts-ctl-%d.csv' % srv_num)
    ctl_data = np.genfromtxt(ctl_csv, delimiter=',')
    ins_csv = os.path.join(BASE_PATH, 'sfc-ts-ins-0-%d.csv' % srv_num)
    ins_data = np.genfromtxt(ins_csv, delimiter=',')

    ROUND = ins_data.shape[0]

    for rd in range(ROUND):
        sfc_dl_lst.append(ins_data[rd][0] - ctl_data[rd][0])
        gap_lst.append(ins_data[rd][-2] - ins_data[rd][-1])

    ipdb.set_trace()

    cor_faktor = 1  # depends on the number of tests

    dl_avg = np.average(sfc_dl_lst)
    dl_std = np.std(sfc_dl_lst)
    dl_std_emp = dl_std * cor_faktor
    dl_hwci = (T_FACTOR * dl_std_emp) / np.sqrt(ROUND - 1)
    tl_sfc_dl_lst.append((dl_avg, dl_hwci))

    gap_avg = np.average(gap_lst)
    gap_std = np.std(gap_lst)
    gap_std_emp = gap_std * cor_faktor
    gap_hwci = (T_FACTOR * gap_std_emp) / np.sqrt(ROUND - 1)
    tl_gap_lst.append((gap_avg, gap_hwci))


# SFC creation time
ax_s.bar(
    x, [y[0] for y in tl_sfc_dl_lst], width, alpha=0.8,
    yerr=[y[1] for y in tl_sfc_dl_lst], color='green',
    error_kw=dict(elinewidth=1.5, ecolor='black'),
    label='SFC start time'
)

ax_s.bar(
    x + width, [y[0] for y in tl_gap_lst], width, alpha=0.8,
    yerr=[y[1] for y in tl_gap_lst], color='blue',
    error_kw=dict(elinewidth=1.5, ecolor='black'),
    label='Gap time'
)

ax_s.set_xticks(x + width / 2.0)
ax_s.set_xticklabels(x, fontsize=font_size, fontname=font_name)
ax_s.set_xlim(0, 10)
ax_s.set_xlabel("Number of chained SF-servers",
                fontsize=font_size, fontname=font_name)
ax_s.set_ylabel("Latency (s)", fontsize=font_size, fontname=font_name)

handles, labels = ax_s.get_legend_handles_labels()
ax_s.legend(handles, labels, fontsize=font_size,
            loc='best')

ax_s.grid()

# For multiple node
# fig_m, ax_m = plt.subplots()
# ax_m.set_title("Function: Append time stamp", fontsize=font_size + 1,
#                fontname=font_name)
#
# ax_m.set_xlabel("Number of chained SF-servers",
#                 fontsize=font_size, fontname=font_name)
# ax_m.set_ylabel("Latency (s)", fontsize=font_size, fontname=font_name)
#
# ax_m.grid()
#

fig_s.savefig('./chain_start_latency_result.png', dpi=500, bbox_inches='tight')
# plt.show()
