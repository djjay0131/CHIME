#
# Extra Experiment: Uniform vs Zipfian distribution
# Tests CHIME, Sherman, SMART with uniform distribution (no hotspot)
# to show how Zipfian skew benefits caching
# on YCSB C pattern (100% read) with 9 CN, 64 threads per CN
#
# NOTE: This experiment generates a custom uniform workload on-the-fly
# by modifying the workload spec before YCSB split. The base workload
# files (load phase) are the same; only the txn (run) phase differs.
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
exp_name = 'extra_uniform_dist'

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
methods = ['CHIME', 'Sherman', 'SMART']
distributions = ['zipfian', 'uniform']
workload_name = 'c'  # YCSB C = 100% read
CN_num = 9
client_num_per_CN = 64
MN_num = 1
key_type = 'randint'
value_size = 8
cache_size = 100
target_epoch = 10
span_sizes = {'CHIME': 64, 'Sherman': 64, 'SMART': 1}
epsilon = 16
neighbor_size = 8
hotspot_buffer_size = 30


@print_func_time
def main(cmd: CMDManager, tp: LogParser):
    plot_data = {
        'methods': methods,
        'distributions': distributions,
        'Y_data': {dist: {method: 0 for method in methods} for dist in distributions},
        'BACKUP_data': {dist: {method: 0 for method in methods} for dist in distributions}
    }

    for dist in distributions:
        for method in methods:
            project_dir = f"{home_dir}/{'CHIME' if method == 'Sherman' else method}"
            work_dir = f"{project_dir}/build"
            env_cmd = f"cd {work_dir}"

            sed_cmd = (sed_workloads_dir('./workloads.conf', workloads_dir) + " && " +
                      generate_sed_cmd('./include/Common.h', method, 8, value_size,
                                       cache_size, MN_num, span_sizes[method],
                                       {'epsilon': epsilon, 'neighbor_size': neighbor_size,
                                        'hotspot_buffer_size': hotspot_buffer_size}))
            cmake_option = f'{common_options} {cmake_options[method]}'
            BUILD_PROJECT = f"cd {project_dir} && {sed_cmd} && mkdir -p build && cd build && cmake {cmake_option} .. && make clean && make -j"

            cmd.all_execute(BUILD_PROJECT)

            # For uniform distribution, we use a modified workload name
            # The split_workload.py will use the txn file which has uniform access pattern
            # We need to generate it if it doesn't exist
            wl_name = workload_name if dist == 'zipfian' else f'{workload_name}_uniform'

            if dist == 'uniform':
                # Generate uniform workload txn file on all nodes if needed
                # Use the same load file as zipfian (same data), different txn pattern
                GENERATE_UNIFORM = (
                    f"cd {ycsb_dir} && "
                    f"if [ ! -f workloads/txn_randint_workload{wl_name} ]; then "
                    f"  cp workloads/load_randint_workload{workload_name} workloads/load_randint_workload{wl_name} && "
                    f"  python3 -c \""
                    f"import random; random.seed(42); "
                    f"ops = ['READ'] * 60000000; "
                    f"keys = [random.randint(1, 60000000) for _ in range(60000000)]; "
                    f"f = open('workloads/txn_randint_workload{wl_name}', 'w'); "
                    f"[f.write(f'{{ops[i]}} {{keys[i]}}\\n') for i in range(60000000)]; "
                    f"f.close(); print('Generated uniform workload')"
                    f"\"; "
                    f"fi"
                )
                cmd.all_execute(GENERATE_UNIFORM, CN_num)

            CLEAR_MEMC = f"{env_cmd} && /bin/bash ../script/restartMemc.sh"
            SPLIT_WORKLOADS = f"{env_cmd} && python3 {ycsb_dir}/split_workload.py {wl_name} {key_type} {CN_num} {client_num_per_CN}"
            YCSB_TEST = f"{env_cmd} && ./ycsb_test {CN_num} {client_num_per_CN} 2 {key_type} {wl_name}"
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

            print_GOOD(f"[FINISHED] dist={dist} method={method} tpt={tpt} p99={p99_lat}")
            plot_data['Y_data'][dist][method] = tpt
            plot_data['BACKUP_data'][dist][method] = p99_lat

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
