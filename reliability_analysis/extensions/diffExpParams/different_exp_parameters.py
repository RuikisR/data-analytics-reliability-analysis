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

def simulate(m, n, r, s, end, lam, mu):
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
            lattice[i][j] = reliability_analysis.Node(lam, mu)
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
        system_status = reliability_analysis.check_system(r, s, lattice)
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


def plotAvgDowntimeWithDiffMu(downtimeArrMu, muArr):
    res = []
    for row in downtimeArrMu:
        res.append(row[0])
    # Create a chart
    plt.plot(muArr, downtimeArrMu)

    # Set the horizontal label, vertical label, and title
    plt.xlabel('mu')
    plt.ylabel('average_downtime')
    plt.title('Average Downtime vs. mu')

    # # Display chart
    # plt.show()

    # Save figure
    plt.savefig("different mu")

def plotAvgDowntimeWithDiffLam(downtimeArrLam, lamArr):
    # Create a chart
    plt.plot(lamArr, downtimeArrLam, color='red')

    # Set the horizontal label, vertical label, and title
    plt.xlabel('lam')
    plt.ylabel('average_downtime')
    plt.title('Average Downtime vs. lam')

    # # Display chart
    # plt.show()

    # Save figure
    plt.savefig("different lam")

def plotAvgDowntimeWithDiffParams(downtimeArr, lamArr, muArr):
    # Create a 3D chart
    fig = plt.figure()
    ax = plt.axes(projection='3d')

    # Construction grid
    X, Y = np.meshgrid(lamArr, muArr)

    # Draw a surface diagram
    surf = ax.plot_surface(X, Y, np.array(downtimeArr), cmap='coolwarm')

    # Set horizontal, vertical, and Z-axis labels
    ax.set_xlabel('lam')
    ax.set_ylabel('mu')
    ax.set_zlabel('downtime')

    # Add color bar
    fig.colorbar(surf, shrink=0.5, aspect=5)

    # # Display chart
    # plt.show()

    # Save figure
    plt.savefig("different mu & lam")

def main():
    runs = 100
    end = 50
    # Init downtime array with different mu & lam values of the exponential
    downtimeArr = []
    muArr = []
    lamArr = []
    minLam = -1
    minMu = -1
    minDownTime = 10
    # Load Simulation Settings
    with open("../../exponentialMu.yaml", 'r') as f:
        exponential_mu = yaml.safe_load(f)
    with open("../../exponentialLam.yaml", 'r') as f:
        exponential_lam = yaml.safe_load(f)
    print(exponential_mu)
    print(exponential_lam)
    lamLen = len(exponential_lam['batch_different_lam'])
    for _, mu in exponential_mu['batch_different_mu'].items():
        muArr.append(mu)
        temp = []
        for _, lam in exponential_lam['batch_different_lam'].items():
            if len(lamArr) < lamLen:
                lamArr.append(lam)
            # Number of periods to simulate and metrics
            reliability = []
            # 10000 simulation runs
            for i in range(runs):
                downtime, _, _, _, _ = simulate(3, 3, 2, 2, end, mu, lam)
                reliability.append(downtime)
            if minDownTime > np.mean(reliability):
                minDownTime = np.mean(reliability)
                minMu = mu
                minLam = lam
            temp.append(np.mean(reliability))
        downtimeArr.append(temp)
    print("min Mu:", minMu)
    print("min Lam:", minLam)

    # plot figure
    if len(lamArr) == 1:
        # plot the testing results for different mu value - 2d
        plotAvgDowntimeWithDiffMu(downtimeArr, np.array(muArr))
    elif len(muArr) == 1:
        # plot the testing results for different lam value - 2d
        plotAvgDowntimeWithDiffLam(downtimeArr[0], np.array(lamArr))
    else:
        # plot the testing results for different lam & mu value - 3d
        plotAvgDowntimeWithDiffParams(np.array(downtimeArr), np.array(lamArr), np.array(muArr))


if __name__ == "__main__":
    main()
