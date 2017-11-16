#!/bin/python3
# About: Test IPD(inter-packet delay) limit

import subprocess
import sys
import time
import shlex
import math

payload_len = 512

if sys.argv[1] == '-h':
    print('python3 ./run_ipd_test.py sf_num num_packet ipd test_round')
    sys.exit(0)

sf_num = int(sys.argv[1])
num_packet = int(sys.argv[2])
ipd = float(sys.argv[3])
test_round = int(sys.argv[4])
method = sys.argv[5]

print('SF num:%d, num_packet:%d, ipd:%f' % (sf_num, num_packet, ipd))

# Calc send rate
send_rate = int(math.ceil(payload_len / ipd))
print('Send rate:%d' % send_rate)

output = '-'.join(
    (method, str(send_rate), str(payload_len), str(sf_num), str(test_round))
) + '.csv'
print(output)
cmd = """python3 ./udp_latency.py -c 10.0.12.12:9999 --payload_len %s --send_rate %s --n_packets %s --log_level INFO --output_file %s""" % (
    payload_len, send_rate, num_packet, output)
print(cmd)
cmd_args = shlex.split(cmd)
subprocess.call(cmd_args)
