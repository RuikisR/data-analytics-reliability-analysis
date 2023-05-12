import numpy as np
from queue import PriorityQueue
import math
import yaml
import importlib
import sys
import os
import matplotlib.pyplot as plt
from reliability_analysis import *


def check_system(connect, lattice):
    states = np.array([[int(node.getStatus()) for node in nodes] for nodes in lattice])
    #print(states)
    m = len(lattice)
    n = len(lattice[0])
    points = [[i,j] for i in range(m) for j in range(n)]
    for point1 in points:
        i1 = point1[0]
        j1 = point1[1]
        for point2 in points:
            i2 = point2[0]
            j2 = point2[1]
            for point3 in points:
                i3 = point3[0]
                j3 = point3[1]
                if connect[i1][j1][i2][j2] == 1 and connect[i2][j2][i3][j3] == 1 and connect[i1][j1][i3][j3] == 1:
                    if point1 != point2 and point2 != point3 and point1!=point3:
                        if not lattice[i1][j1].getStatus() and not lattice[i2][j2].getStatus() and not lattice[i3][j3].getStatus():
                            return 0 #Fail
    return 1


def simulate(m, n, end, lam, mu):
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
            lattice[i][j] = Node(lam,mu)
            event_queue.put((lattice[i][j].getNext(), True, m * i + j))
            maintenance_costs += round(cm * lattice[i][j].getNext(), 6)

    # Create connection matrix
    connect = [[[[0 for _ in range(n)] for _ in range(m)] for _ in range(n)] for _ in range(m)]

    for j in range(m):
        for i in range(n):
            connect[i][j][i - 1][j - 1] = 1
            connect[i][j][i - 1][j] = 1
            connect[i][j][i][j - 1] = 1
            if j < n - 1:
                connect[i][j][i][j + 1] = 1
                if i < n - 1:
                    connect[i][j][i + 1][j + 1] = 1
                else:
                    connect[i][j][0][j + 1] = 1
            else:
                connect[i][j][i][0] = 1
                if i < n - 1:
                    connect[i][j][i + 1][0] = 1
                else:
                    connect[i][j][0][0] = 1
            if i < n - 1:
                connect[i][j][i + 1][j] = 1
            else:
                connect[i][j][0][j] = 1
    # Simulation
    while t < end:
        #print(t)
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
        system_status = check_system(connect,lattice)
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
    with open("lattice_structure.yaml", 'r') as f:
        config = yaml.safe_load(f)

    for i, (batch_name, batch) in enumerate(config.items()):
        print(f"Simulating Batch {i + 1} of {len(config)} - {batch_name}")
        m = batch["m"]
        n = batch["n"]

        end = 30
        runs = 100
        #lam = 5
        #mu = 2

        # Prepare lists for storing the results
        reliability = []
        MTTF = []
        MTBF = []
        avg_r = []
        avg_m = []

        # Run the simulations
        for lam in [5,10,15]:
            for mu in [0.5,2,10]:
                print(lam,mu)
                for run in range(runs):
                    #print(run)
                    downtime, TTF, TBF, repair_costs, maintenance_costs = simulate(m, n, end, lam, mu)
                    reliability.append(downtime)
                    MTTF.append(TTF)
                    MTBF.append(TBF)
                    avg_r.append(repair_costs)
                    avg_m.append(maintenance_costs)
                # Calculate averages
                print(1-np.mean(reliability))
                #print("MTTF", str(np.mean(MTTF)))
                #print("MTBF", str(np.mean(MTBF)))
                print((np.mean(avg_r) + np.mean(avg_m)) / (np.mean(reliability) * end))
                #print("avg_r", str(np.mean(avg_r)))
                #print("avg_m", str(np.mean(avg_m)))


if __name__ == "__main__":
    main()
