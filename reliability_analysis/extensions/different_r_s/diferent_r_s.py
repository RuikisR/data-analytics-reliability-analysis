import copy

import numpy as np
from queue import PriorityQueue
import yaml
import importlib
import sys
import os
import matplotlib.pyplot as plt
import matplotlib
from reliability_analysis import reliability_analysis
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt


def plot_xy(x, y, xlabel, ylabel, title, filename=None):
    plt.clf()
    plt.plot(x, y)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    if filename:
        plt.savefig(filename)


def main():
    # Load Simulation Settings
    with open("../../../different_rs.yaml", 'r') as f:
        config = yaml.safe_load(f)
    print(config)
    r = []
    s = []
    bp = []
    re = []
    mttf = []
    mtbf = []
    avgr = []
    avgm = []

    for i, (batch_name, batch) in enumerate(config.items()):
        print(f"Simulating Batch {i + 1} of {len(config)} - {batch_name}")
        for module_name in batch['extension_modules']:
            spec = importlib.util.spec_from_file_location(module_name,
                                                          os.path.join("../../../reliability_analysis", "extensions",
                                                                       module_name, module_name + ".py"))
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        # Number of periods to simulate and metrics
        end = 50
        reliability = []
        MTTF = []
        MTBF = []
        avg_r = []
        avg_m = []
        # 10000 simulation runs
        for i in range(100):
            downtime, TTF, TBF, repair_costs, maintenance_costs = reliability_analysis.simulate(6, 6, batch['r'], batch['s'], end, 15, 15)
            reliability.append(downtime)
            MTTF.append(TTF)
            MTBF.append(TBF)
            avg_r.append(repair_costs)
            avg_m.append(maintenance_costs)
        reliability = 1 - np.mean(reliability)
        MTTF = np.mean(MTTF)
        MTBF = np.mean(MTBF)
        avg_r = round(np.mean(avg_r), 6)
        avg_m = round(np.mean(avg_m), 6)
        breakeven_profit = round((avg_r + avg_m) / (reliability * end), 6)
        r.append(batch['r'])
        s.append(batch['s'])
        bp.append(breakeven_profit)
        re.append(reliability)
        mttf.append(MTTF)
        mtbf.append(MTBF)
        avgr.append(avg_r)
        avgm.append(avg_m)
        for module in batch['extension_modules']:
            del sys.modules[module]

    plot_xy(r, bp, 'r', 'breakeven_profit', 'Change of breakeven_profit when r change', 'r_bp')
    plot_xy(r, re, 'r', 'reliability', 'Change of reliability when r change', 'r_re')
    plot_xy(r, mttf, 'r', 'MTTF', 'Change of MTTF when r change', 'r_mttf')
    plot_xy(r, mtbf, 'r', 'MTBF', 'Change of MTBF when r change', 'r_mtbf')
    plot_xy(r, avgr, 'r', 'Average of Repair Costs', 'Change of Average of Repair Costs when r change', 'r_avgr')
    plot_xy(r, avgm, 'r', 'Average of Maintenance Costs', 'Change of Average of Maintenance Costs when r change', 'r_avgm')

if __name__ == "__main__":
    main()