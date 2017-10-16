#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Plot Results of Latency Measurements

Email: xianglinks@gmail.com
"""


import os

import numpy as np

import matplotlib.pyplot as plt
import matplotlib as mpl

BASE_PATH = './test_result/single_node/'

SEND_RATE = 1000  # byte/s
PAYLOAD_LEN = 512  # byte
NUM_PACKETS = 10000

MAX_FS_NUM = 10


font_size = 10
# Match the latex template
font_name = 'Universalis ADF Cd Std'

mpl.rc('font', family=font_name)
# mpl.use('TkAgg')

fig, ax = plt.subplots()

# fig.suptitle('Latency(RTT) for UDP Packets', fontsize=13)
ax.set_title("Service Function: Simple IP Forwarding", fontsize=font_size + 1,
             fontname=font_name)

x = np.arange(0, MAX_FS_NUM + 1, 1, dtype='int32')
width = 0.35

T_FACTOR = 2.678  # 99% for two sided

for method, color, label, pos in zip(
    ('lkf', 'pyf'), ('blue', 'green'),
    ('Kernel forwarding', 'Python forwarding'),
    (0, width)
):
    base_file_name = '-'.join(
        map(str, (method, NUM_PACKETS, SEND_RATE, PAYLOAD_LEN))
    )
    lat_avg_lst = []
    lat_hwci_lst = []
    for srv_num in range(0, MAX_FS_NUM + 1):
        csv_path = os.path.join(BASE_PATH,
                                base_file_name + '-%d.csv' % srv_num)
        data = np.genfromtxt(csv_path, delimiter=',')
        lat = data[1:, 1] / 1000.0
        lat_avg_lst.append(np.average(lat))
        lat_std = np.std(lat)
        # Calc empirical std
        emp_lat_std = (
            np.sqrt(float(NUM_PACKETS - 1)) / (NUM_PACKETS - 2)
        ) * lat_std
        lat_hwci = (T_FACTOR * emp_lat_std) / np.sqrt(NUM_PACKETS - 1)
        lat_hwci_lst.append(lat_hwci)

    y = lat_avg_lst

    ax.plot(x + pos + width / 2, y,
            marker='o', markerfacecolor='None', markeredgewidth=1,
            markeredgecolor=color, color=color, lw=1, ls='--')

    ax.bar(x + pos, y, width, label=label, color=color)

ax.set_xlabel("Number of chained SF-servers",
              fontsize=font_size, fontname=font_name)
ax.set_xticks(x + width)
ax.set_xticklabels(x, fontsize=font_size, fontname=font_name)
ax.set_xlim(0, 11)
ax.set_yticks(range(0, 7))
ax.set_yticklabels(range(0, 7), fontsize=font_size, fontname=font_name)
ax.set_ylabel("RTT (ms)", fontsize=font_size, fontname=font_name)
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels, fontsize=font_size,
          loc='upper left')
ax.grid()

fig.show()
# fig.savefig('./udp_latency_rtt.eps', format='eps', bbox_inches='tight')
plt.show()
