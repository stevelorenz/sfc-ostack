#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Data processing and try to find errors...

Email: xianglinks@gmail.com
"""

import os
import sys

import ipdb
import numpy as np


def print_std_err(test_round):
    """Print standard error of the results

    Used to check if more test rounds are needed
    """

    min_sf_num = 1
    max_sf_num = 10
    method_tuple = ('ns', 'fn', 'nsrd')
    base_path = './test_result/three_compute/'
    result_map = dict()

    ts_info_tuple = (
        'SI launching time',
        'SFP waiting time',
        'SFC reordering time',
        'PC building time'
    )

    for method in method_tuple:
        start_time_stderr = list()
        gap_time_stderr = list()
        for srv_num in range(min_sf_num, max_sf_num + 1):
            ctl_fn = '%s-sfc-ts-ctl-%d.csv' % (method, srv_num)
            ctl_csvp = os.path.join(base_path, ctl_fn)
            ctl_data = np.genfromtxt(ctl_csvp, delimiter=',')
            if ctl_data.shape[0] < test_round:
                raise RuntimeError(
                    'Number of test rounds is wrong, path: %s' % ctl_csvp
                )
            std_err_lst = list()
            for t_idx, t_name in enumerate(ts_info_tuple):
                std_err_lst.append(
                    np.std(ctl_data[:, t_idx]) / np.sqrt(test_round)
                )
            start_time_stderr.append(std_err_lst)

            ins_fn = '%s-sfc-ts-ins-%d.csv' % (method, srv_num)
            ins_csvp = os.path.join(base_path, ins_fn)
            ins_data = np.genfromtxt(ins_csvp, delimiter=',')
            if ins_data.shape[0] < test_round:
                raise RuntimeError(
                    'Number of test rounds is wrong, path: %s' % ins_csvp
                )
            if ins_data.shape[1] != srv_num + 4:
                raise RuntimeError(
                    'Number of timestamps is wrong, path: %s' % ins_csvp
                )
            gap_time_stderr.append(
                np.std(np.subtract(
                    ins_data[:, -2], ins_data[:, -1])) / np.sqrt(test_round)
            )

        result_map[method] = (start_time_stderr, gap_time_stderr)

    # Try to print pretty
    for method, err_tpl in result_map.items():
        print('# Method: %s' % method)
        st_err, gap_err = err_tpl
        print('## Start time error: %s' % ', '.join(ts_info_tuple))
        for idx, err in enumerate(st_err):
            print('Srv_num %d: %s' % (idx + 1, ', '.join(map(str, err))))
        print(1 * '\n')
        print('## Gap time error: ')
        for idx, err in enumerate(gap_err):
            print('Srv_num %d: %s' % (idx + 1, err))
        print(2 * '\n')


if __name__ == "__main__":
    print_std_err(10)
