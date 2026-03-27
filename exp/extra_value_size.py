#
# Extra Experiment: Value size scaling
# Tests CHIME, Sherman, SMART, ROLEX with value sizes 8B, 64B, 256B
# on YCSB A (50% read, 50% update) with 9 CN, 32 threads per CN
#
from func_timeout import FunctionTimedOut
from pathlib import Path
import json

from utils.cmd_manager import CMDManager
from utils.log_parser import LogParser
from utils.sed_generator import sed_workloads_dir, generate_sed_cmd
from utils.color_printer import print_GOOD, print_WARNING
from utils.func_timer import print_func_time


input_path = './params'
output_path = './results'
exp_name = 'extra_value_size'

# common params
with (Path(input_path) / 'common.json').open(mode='r') as f:
    params = json.load(f)
home_dir      = params['home_dir']
workloads_dir = params['workloads_dir']
ycsb_dir      = str(Path(workloads_dir).parent)
cluster_ips   = params['cluster_ips']
master_ip     = params['master_ip']
common_options= params['common_options']
cmake_options = params['cmake_options']

# experiment config
methods = ['CHIME', 'Sherman', 'SMART', 'ROLEX']
value_sizes = [8, 64, 256]  # bytes
workload_name = 'a'  # YCSB A = 50/50 read/update
CN_num = 9
client_num_per_CN = 32
MN_num = 1
key_type = 'randint'
cache_size = 100
target_epoch = 10
span_sizes = {'CHIME': 64, 'Sherman': 64, 'SMART': 1, 'ROLEX': 16}
epsilon = 16
neighbor_size = 8
hotspot_buffer_size = 30


@print_func_time
def main(cmd: CMDManager, tp: LogParser):
    plot_data = {
        'methods': methods,
        'value_sizes': value_sizes,
        'X_data': {method: [] for method in methods},
        'Y_data': {method: [] for method in methods},    # throughput
        'BACKUP_data': {method: [] for method in methods} # p99 latency
    }

    for val_size in value_sizes:
        for method in methods:
            project_dir = f"{home_dir}/{'CHIME' if method == 'Sherman' else method}"
            work_dir = f"{project_dir}/build"
            env_cmd = f"cd {work_dir}"

            sed_cmd = (sed_workloads_dir('./workloads.conf', workloads_dir) + " && " +
                      generate_sed_cmd('./include/Common.h', method, 8, val_size,
                                       cache_size, MN_num, span_sizes[method],
                                       {'epsilon': epsilon, 'neighbor_size': neighbor_size,
                                        'hotspot_buffer_size': hotspot_buffer_size}))
            cmake_option = f'{common_options} {cmake_options[method]}'
            BUILD_PROJECT = f"cd {project_dir} && {sed_cmd} && mkdir -p build && cd build && cmake {cmake_option} .. && make clean && make -j"

            cmd.all_execute(BUILD_PROJECT)

            CLEAR_MEMC = f"{env_cmd} && /bin/bash ../script/restartMemc.sh"
            SPLIT_WORKLOADS = f"{env_cmd} && python3 {ycsb_dir}/split_workload.py {workload_name} {key_type} {CN_num} {client_num_per_CN}"
            YCSB_TEST = f"{env_cmd} && ./ycsb_test {CN_num} {client_num_per_CN} 2 {key_type} {workload_name}"
            KILL_PROCESS = f"{env_cmd} && killall -9 ycsb_test"

            cmd.all_execute(SPLIT_WORKLOADS, CN_num)
            while True:
                try:
                    cmd.all_execute(KILL_PROCESS, CN_num)
                    cmd.one_execute(CLEAR_MEMC)
                    logs = cmd.all_long_execute(YCSB_TEST, CN_num, only_need_tpt=True)
                    tpt, _, _, _, _, _, _ = tp.get_statistics(logs, target_epoch, get_avg=True)
                    p50_lat, p99_lat = cmd.get_cluster_lats(str(Path(project_dir) / 'us_lat'), CN_num, target_epoch, get_avg=True)
                    break
                except (FunctionTimedOut, Exception) as e:
                    print_WARNING(f"Error! Retry... {e}")

            print_GOOD(f"[FINISHED] val_size={val_size}B method={method} tpt={tpt} p99={p99_lat}")
            plot_data['X_data'][method].append(val_size)
            plot_data['Y_data'][method].append(tpt)
            plot_data['BACKUP_data'][method].append(p99_lat)

    # save
    Path(output_path).mkdir(exist_ok=True)
    with (Path(output_path) / f'{exp_name}.json').open(mode='w') as f:
        json.dump(plot_data, f, indent=2)


if __name__ == '__main__':
    cmd = CMDManager(cluster_ips, master_ip)
    tp = LogParser()
    t = main(cmd, tp)
    with (Path(output_path) / 'time.log').open(mode="a+") as f:
        f.write(f"{exp_name}.py execution time: {int(t//60)} min {int(t%60)} s\n")
