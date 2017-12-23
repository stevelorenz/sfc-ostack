#!/bin/bash
#
# About: Plot all plots for evaluation results

sp_dir=$(pwd)

# UDP Ony-way Delay
cd "../udp_latency/one_way/" || exit
python3 ./plot.py
mv ./*.pdf "$sp_dir/"

# UDP OWD
cd "$sp_dir/../udp_latency/owd/" || exit
python3 ./plot.py l
python3 ./plot.py p
python3 ./plot.py as
mv ./*.pdf "$sp_dir/"

# UDP RTT
cd "$sp_dir/../udp_latency/rtt/" || exit
python3 ./plot.py -a
mv ./*.pdf "$sp_dir/"

# Start and gap time
cd "$sp_dir/../sfc_start_latency/" || exit
python3 ./plot.py -mg
python3 ./plot.py -msw
mv ./*.pdf "$sp_dir/"
