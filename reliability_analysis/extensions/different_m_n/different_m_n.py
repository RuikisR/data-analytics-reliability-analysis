import copy
import csv
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
    with open("../../../different_mn.yaml", 'r') as f:
        config = yaml.safe_load(f)
    print(config)

    results = []

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
            downtime, TTF, TBF, repair_costs, maintenance_costs = reliability_analysis.simulate(6, 6, batch['m'], batch['n'], end, 15, 15)
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
      
        for module in batch['extension_modules']:
            del sys.modules[module]
        results.append([f"m={batch['m']}",f"n={batch['n']}", breakeven_profit, reliability, MTTF, MTBF, avg_r, avg_m])

    # Write results to a csv file
        with open('results.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["value of m", "value of n", "breakeven profit", "reliability", "MTTF", "MTBF", "avg_r", "avg_m"])
            writer.writerows(results)

if __name__ == "__main__":
    main()
