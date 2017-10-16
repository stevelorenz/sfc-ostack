#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Plot results of chain creation latency tests

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

BASE_PATH = './test_result/'

MAX_FS_NUM = 1
x = np.arange(0, MAX_FS_NUM + 1, 1, dtype='int32')
width = 0.35


#############
#  Ploting  #
#############

# color map for SF latency
cmap = plt.get_cmap('hsv')

fig, ax = plt.subplots()
ax.set_title("Service Function: Append time stamp", fontsize=font_size + 1,
             fontname=font_name)

for srv_num in range(1, MAX_FS_NUM + 1):
    csv_path = os.path.join(BASE_PATH,
                            'cen-pyf-%d-cctime-pm.csv' % srv_num)
    data = np.genfromtxt(csv_path)
    import ipdb
    ipdb.set_trace()
    # ts_s
    # Last recv A packet
    # ts_l

ax.bar([1], [2], width, color=cmap(0.1))
ax.bar([1], [1], width, color=cmap(0.2))

# MARK: Plot SF latency and chain creation(CC) latency


ax.set_xlabel("Number of chained SF-servers",
              fontsize=font_size, fontname=font_name)
ax.set_ylabel("Latency (s)", fontsize=font_size, fontname=font_name)

ax.grid()
fig.savefig('./chain_start_latency_result.png', dpi=500, bbox_inches='tight')
