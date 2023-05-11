import numpy as np
from queue import PriorityQueue
import math
import yaml
import importlib
import sys
import os
import matplotlib.pyplot as plt
from reliability_analysis import *


def plot_3d(x, y, z, xlabel, ylabel, zlabel, title, label, ax):
    sc = ax.scatter(x, y, z, label=label)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_zlabel(zlabel)
    ax.set_title(title)
    ax.legend()


def check_system(r, s, lattice, wrap=False):
    m = len(lattice)
    n = len(lattice[0])

    if wrap == True:
        # Building transformed matrix
        transformed_matrix = []
        flag = 0
        for i in range(m):
            transformed_row = []
            for j in range(n + s - 1):
                # Scan the lattice for dangerous rows, hopping over columns' end
                if not lattice[i % m][j % n].getStatus():
                    flag += 1
                    if flag == s:
                        transformed_row.append((j - s + 1) % n)
                        flag -= 1
                else:
                    flag = 0
            transformed_matrix.append(transformed_row)
        # Scan transformed matrix to see if it's broken, hopping over rows' end
        for row in range(m + r - 1):
            # Build intersection of the r rows
            init_set = set(transformed_matrix[row % m])
            for more in range(r):
                init_set = init_set & set(transformed_matrix[(row + more) % m])
            if (init_set):
                return 0
        return 1
    
    else:
        # Building transformed matrix
        transformed_matrix = []
        flag = 0
        for i in range(m):
            transformed_row = []
            for j in range(n - s + 1):
                # Scan the lattice for dangerous rows
                if not lattice[i][j].getStatus():
                    flag += 1
                    if flag == s:
                        transformed_row.append(j - s + 1)
                        flag -= 1
                else:
                    flag = 0
            transformed_matrix.append(transformed_row)

        # Scan transformed matrix to see if it's broken
        for row in range(m - r + 1):
            # Build intersection of the r rows
            init_set = set(transformed_matrix[row])
            for more in range(1, r):
                init_set = init_set & set(transformed_matrix[row + more])
            if init_set:
                return 0
        return 1


def simulate(m, n, r, s, end, lam, mu, wrap):
    # Cost parameters
    cr = 0.5
    cm = 0.25
    # Initiate clock, counters, and a false failure indicator
    t = 0
    fail_flag = 0
    TTF = end
    TBF = 0
    TBF_history = []
    total_downtime = 0
    repair_costs = 0
    maintenance_costs = 0
    # Initiate queue of failures and repairs
    event_queue = PriorityQueue()
    # Create latice and fill with nodes, record planned failures
    lattice = np.empty((m, n), dtype=object)
    for i in range(m):
        for j in range(n):
            lattice[i][j] = Node()
            event_queue.put((lattice[i][j].getNext(), True, m * i + j))
            maintenance_costs += round(cm * lattice[i][j].getNext(), 6)
    # Simulation
    while t < end:
        # Get features of next event
        next_time, next_status, next_node = event_queue.get()
        i = next_node // m
        j = next_node % n
        # Update node and event queue (making event happen)
        lattice[i][j].update(not next_status, next_time)
        event_queue.put((lattice[i][j].getNext(), lattice[i][j].getStatus(), m * i + j))
        # Update costs depending on node event
        if lattice[i][j].getStatus():
            maintenance_costs += round(cm * lattice[i][j].getNext(), 6)
        else:
            repair_costs += cr
        # Check system status and update counters
        system_status = check_system(r, s, lattice, wrap)
        if system_status == 0 and TTF == end:
            TTF = next_time
        if system_status == 0:
            if fail_flag:
                total_downtime += next_time - t
            else:
                TBF += next_time - t
                TBF_history.append(TBF)
                fail_flag = 1
                TBF = 0
        else:
            if fail_flag:
                total_downtime += next_time - t
                fail_flag = 0
            else:
                TBF += next_time - t
        # Advance clock
        t = min(next_time, end)
    # If the system never failed, TBF and TTF are set to the simulated time span
    if not TBF_history:
        TBF_history.append(end)
    return (
        total_downtime / end,
        TTF,
        np.mean(TBF_history),
        repair_costs,
        maintenance_costs,
    )


def main():
    # Load Simulation Settings from wrapping.yaml
    with open("../../../wrapping.yaml", 'r') as f:
        config = yaml.safe_load(f)

    # Prepare data storage for both wrapped and non-wrapped cases
    data = {
        "wrapped": {
            "breakeven_profit": [],
            "reliability": [],
            "MTTF": [],
            "MTBF": [],
            "avg_r": [],
            "avg_m": []
        },
        "non_wrapped": {
            "breakeven_profit": [],
            "reliability": [],
            "MTTF": [],
            "MTBF": [],
            "avg_r": [],
            "avg_m": []
        },
        "r": [],
        "s": [],
        "m": [],
        "n": []
    }

    for i, (batch_name, batch) in enumerate(config.items()):
        print(f"Simulating Batch {i + 1} of {len(config)} - {batch_name}")
        m = batch["m"]
        n = batch["n"]
        r = batch["r"]
        s = batch["s"]

        # Store r, s, m, and n values
        data["r"].append(r)
        data["s"].append(s)
        data["m"].append(m)
        data["n"].append(n)

        for wrap in [True, False]:
            end = 50
            runs = 100
            lam = 15
            mu = 15

            # Prepare lists for storing the results
            reliability = []
            MTTF = []
            MTBF = []
            avg_r = []
            avg_m = []

            # Run the simulations
            for _ in range(runs):
                downtime, TTF, TBF, repair_costs, maintenance_costs = simulate(m, n, r, s, end, lam, mu, wrap)
                reliability.append(downtime)
                MTTF.append(TTF)
                MTBF.append(TBF)
                avg_r.append(repair_costs)
                avg_m.append(maintenance_costs)

            # Calculate averages
            prefix = "wrapped" if wrap else "non_wrapped"
            data[prefix]["breakeven_profit"].append((np.mean(avg_r) + np.mean(avg_m)) / (np.mean(reliability) * end))
            data[prefix]["reliability"].append(np.mean(reliability))
            data[prefix]["MTTF"].append(np.mean(MTTF))
            data[prefix]["MTBF"].append(np.mean(MTBF))
            data[prefix]["avg_r"].append(np.mean(avg_r))
            data[prefix]["avg_m"].append(np.mean(avg_m))

    # Plot the results
    labels = ["breakeven_profit",
              "reliability",
              "MTTF",
              "MTBF",
              "avg_r",
              "avg_m"
              ]

    fig = plt.figure(figsize=(12, 8))

    for i, label in enumerate(labels):
        ax = fig.add_subplot(2, 3, i + 1, projection='3d')
        x_wrapped = [r for r in data["r"]]
        y_wrapped = [m for m in data["m"]]
        z_wrapped = data["wrapped"][label]

        x_non_wrapped = [r for r in data["r"]]
        y_non_wrapped = [m for m in data["m"]]
        z_non_wrapped = data["non_wrapped"][label]

        # Plot wrapped and non_wrapped data
        plot_3d(x_wrapped, y_wrapped, z_wrapped, '(r,s)', '(m,n)', label, f"{label} Comparison: Wrapped", "Wrapped", ax)
        plot_3d(x_non_wrapped, y_non_wrapped, z_non_wrapped, '(r,s)', '(m,n)', label,
                f"{label} Comparison: Non-Wrapped",
                "Non-Wrapped", ax)
        ax.grid()

    plt.tight_layout()
    plt.show()

    # for wrap in [True, False]:
    #     prefix = "wrapped" if wrap else "non_wrapped"
    #     print(f"Wrap: {wrap}")
    #     for label in data[prefix]:
    #         print(f"{label}: {data[prefix][label]}")


if __name__ == "__main__":
    main()
