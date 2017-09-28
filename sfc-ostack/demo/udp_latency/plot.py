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

###############
#  Data Proc  #
###############

BASE_PATH = './test_result/'

SEND_RATE = 1000  # byte/s
PAYLOAD_LEN = 512  # byte
NUM_PACKETS = 10000

MAX_FS_NUM = 9

base_file_name = '-'.join(
    map(str, ('lkf', NUM_PACKETS, SEND_RATE, PAYLOAD_LEN))
)

T_FACTOR = 2.678  # 99% for two sided

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

##################
#  Plot Results  #
##################

plt.suptitle('Latency(RTT) for UDP Packets', fontsize=13)

ax1 = plt.subplot(1, 1, 1)
plt.title("Network Function: Simple IP Forwarding", fontsize=9)
x = np.arange(0, MAX_FS_NUM + 1, 1, dtype='int32')
y = lat_avg_lst
# plt.errorbar(x, y, yerr=lat_hwci_lst,
# marker='o', markerfacecolor='None', markeredgewidth=1,
# markeredgecolor='black', color='black', lw=1, ls='-')
plt.plot(x, y,
         marker='o', markerfacecolor='None', markeredgewidth=1,
         markeredgecolor='black', color='black', lw=1, ls='-')
plt.xlabel("Number of chained SF-servers", fontsize=10)
plt.xticks(range(0, MAX_FS_NUM + 2))
plt.ylabel("RTT (ms)", fontsize=10)
# handles, labels = ax1.get_legend_handles_labels()
# ax1.legend(handles, labels, fontsize=8)
plt.grid()

plt.savefig('./udp_latency_result.png', dpi=300)
