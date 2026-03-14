#!/usr/bin/env python3
"""
Minimal smoke test: 1 CN + 1 MN, CHIME, YCSB C.
Verifies: RDMA connectivity, memcached, build, and non-zero throughput.

Run from master node: cd ~/CHIME/exp && python3 smoke_test.py

Prerequisites:
  - common.json configured with cluster_ips (need >= 2 nodes)
  - memcached.conf has master_ip on line 1, 11211 on line 2
  - YCSB workloads generated (run generate_full_workloads.sh or generate_small_workloads.sh)
"""
from pathlib import Path
import json
import sys

# Add exp dir for utils
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.cmd_manager import CMDManager
from utils.log_parser import LogParser
from utils.sed_generator import sed_workloads_dir, generate_sed_cmd
from utils.color_printer import print_GOOD, print_WARNING

input_path = Path(__file__).parent / 'params'
with (input_path / 'common.json').open() as f:
    params = json.load(f)

home_dir = params['home_dir']
workloads_dir = params['workloads_dir']
ycsb_dir = str(Path(workloads_dir).parent)
cluster_ips = params['cluster_ips']
master_ip = params['master_ip']
common_options = params['common_options']
cmake_options = params['cmake_options']

if len(cluster_ips) < 2:
    print("Need at least 2 nodes (1 MN + 1 CN). Edit cluster_ips in common.json.")
    sys.exit(1)

CN_num = 1
client_num_per_CN = 4
MN_num = 1
method = 'CHIME'
workload_name = 'c'
key_type = 'randint'
value_size = 8
cache_size = 100
span_size = 64
neighbor_size = 8
hotspot_buffer_size = 30
target_epoch = 10

project_dir = f"{home_dir}/CHIME"
work_dir = f"{project_dir}/build"
env_cmd = f"cd {work_dir}"

sed_cmd = (
    sed_workloads_dir('./workloads.conf', workloads_dir) + " && " +
    generate_sed_cmd(
        './include/Common.h', method, 8, value_size, cache_size, MN_num, span_size,
        {'epsilon': 16, 'neighbor_size': neighbor_size, 'hotspot_buffer_size': hotspot_buffer_size}
    )
)
cmake_option = f'{common_options} {cmake_options[method]}'
cmake_option = cmake_option.replace('-DMIDDLE_TEST_EPOCH=off', '-DMIDDLE_TEST_EPOCH=on')

BUILD_PROJECT = f"cd {project_dir} && {sed_cmd} && mkdir -p build && cd build && cmake {cmake_option} .. && make clean && make -j"
CLEAR_MEMC = f"{env_cmd} && /bin/bash ../script/restartMemc.sh"
SPLIT_WORKLOADS = f"{env_cmd} && python3 {ycsb_dir}/split_workload.py {workload_name} {key_type} {CN_num} {client_num_per_CN}"
# 2 total nodes (1 MN + 1 CN), 4 threads, 2 coros
YCSB_TEST = f"{env_cmd} && ./ycsb_test 2 {client_num_per_CN} 2 {key_type} {workload_name}"
KILL_PROCESS = f"{env_cmd} && killall -9 ycsb_test"

print("=== CHIME Smoke Test (1 CN + 1 MN, YCSB C) ===")
cmd = CMDManager(cluster_ips, master_ip)
tp = LogParser()

print("Building CHIME...")
cmd.all_execute(BUILD_PROJECT, 2)

print("Splitting workloads...")
cmd.all_execute(SPLIT_WORKLOADS, CN_num)

for attempt in range(3):
    try:
        print("Killing any existing ycsb_test...")
        cmd.all_execute(KILL_PROCESS, 2)
        print("Restarting memcached...")
        cmd.one_execute(CLEAR_MEMC)
        print("Running YCSB C...")
        logs = cmd.all_long_execute(YCSB_TEST, 2, only_need_tpt=True)
        tpt, _, _, _, _, _, _ = tp.get_statistics(logs, target_epoch, get_avg=True)
        cmd.all_execute(KILL_PROCESS, 2)
        break
    except Exception as e:
        print_WARNING(f"Attempt {attempt + 1} failed: {e}. Retrying...")
else:
    print("Smoke test FAILED after 3 attempts.")
    sys.exit(1)

if tpt > 0:
    print_GOOD(f"Smoke test PASSED. Throughput: {tpt:.2f} Mops/s")
else:
    print_WARNING(f"Smoke test completed but throughput is 0. Check RDMA and memcached.")
    sys.exit(1)
