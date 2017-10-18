#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Plot results of chain start latency tests

Email: xianglinks@gmail.com
"""

import os

import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt

font_size = 10
# Match the latex template
font_name = 'Universalis ADF Cd Std'
mpl.rc('font', family=font_name)

MAX_FS_NUM = 1
x = np.arange(0, MAX_FS_NUM + 1, 1, dtype='int32')
width = 0.35

T_FACTOR = 2.678  # 99% for two sided, student distribution

#############
#  Ploting  #
#############

# color map for SF latency
cmap = plt.get_cmap('hsv')

# For single node
fig_s, ax_s = plt.subplots()
ax_s.set_title("Service Function: Append time stamp", fontsize=font_size + 1,
               fontname=font_name)

BASE_PATH = './test_result/single_node/'

############
#  Mode 0  #
############

# To be calculated parameter
# 1. SFC start delay(inclusive SF creation time)
# 2. SFC start gap
tl_st_dl_lst = list()
tl_st_gap_lst = list()
for srv_num in range(1, MAX_FS_NUM + 1):
    ts_len = 3 + 2 * srv_num
    st_dl_lst = list()
    st_gap_lst = list()

    ctl_csv = os.path.join(BASE_PATH, 'sfc-ts-ctl-%d.csv' % srv_num)
    ctl_data = np.genfromtxt(ctl_csv, delimiter=',')
    ins_csv = os.path.join(BASE_PATH, 'sfc-ts-ins-0-%d.csv' % srv_num)
    ins_data = np.genfromtxt(ins_csv, delimiter=',')

    ROUND = ins_data.shape[0]

    for rd in range(ROUND):
        st_dl_lst.append(ins_data[rd][-2] - ctl_data[rd])
        st_gap_lst.append(ins_data[rd][-2] - ins_data[rd][0])

    gap_avg = np.average(st_gap_lst)
    gap_std = np.std(st_gap_lst)
    cor_faktor = 1  # depends on the number of tests
    gap_std_emp = gap_std * cor_faktor
    gap_hwci = (T_FACTOR * gap_std_emp) / np.sqrt(ROUND - 1)

    tl_st_gap_lst.append((gap_avg, gap_hwci))
    import ipdb
    ipdb.set_trace()

    # ax_s.bar([1], [2], width, color=cmap(0.1))
    # ax_s.bar([1], [1], width, color=cmap(0.2))

# MARK: Plot SF latency and chain creation(CC) latency

ax_s.set_xlabel("Number of chained SF-servers",
                fontsize=font_size, fontname=font_name)
ax_s.set_ylabel("Latency (s)", fontsize=font_size, fontname=font_name)

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

# fig_m.savefig('./chain_start_latency_result.png', dpi=500, bbox_inches='tight')
plt.show()
