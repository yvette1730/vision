#!/bin/bash

clear
echo running multinode
# Read the lines of the file into an array
mapfile -t NODES < $PBS_NODEFILE
# $COBALT_NODEFILE

# Print the array to the console
# printf '%s\n' "${NODES[@]}"

for((rank=0;rank<${#NODES[*]};rank++));
do
    ssh ${NODES[rank]} ~/cs/vision/_multinode.sh "<yaml>" ${#NODES[*]} $rank ${NODES[0]} $PBS_NODEFILE &
done
