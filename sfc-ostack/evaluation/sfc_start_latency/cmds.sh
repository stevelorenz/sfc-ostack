#!/bin/bash
# About: List of useful commands for time measurements

echo "# Current time in miliseconds:"
echo $(($(date +%s%N)/1000000))
