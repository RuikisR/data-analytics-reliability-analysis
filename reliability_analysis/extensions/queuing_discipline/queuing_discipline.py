import numpy as np
from queue import PriorityQueue
import math
import yaml
import importlib
import sys
import os
import pandas as pd

SMART_REPAIR = False


class Node:
    def __init__(self, lam=10, mu=10):
        # Uptime rate (lam) and downtime rate (mu); they give average periods until event
        self.__status = True
        self.__next_event = np.random.exponential(lam)
        self.__lam = lam
        self.__mu = mu

    def enable(self, current_time):
        self.__status = True
        self.__next_event = current_time + np.random.exponential(self.__lam)

    def disable(self):
        self.__status = False

    def repair(self, current_time):
        self.__next_event = current_time + np.random.exponential(self.__mu)

    def get_online(self):
        return self.__status

    def get_time(self):
        return self.__next_event


def get_system_status(r, s, lattice, smart=SMART_REPAIR):
    m = len(lattice)
    n = len(lattice[0])
    # Building transformed matrix
    transformed_matrix = np.zeros((m - r + 1, n - s + 1))
    for i in range(len(transformed_matrix)):
        for j in range(len(transformed_matrix[0])):
            # Scan the lattice for dangerous rows, hopping over columns' end
            for x in range(r):
                for y in range(s):
                    if not lattice[(i + x) % m][(j + y) % n].get_online():
                        transformed_matrix[i][j] += 1
    # Scan transformed matrix to see if it's broken, hopping over rows' end
    if smart:
        prio_matrix = np.zeros((m, n))
        for i in range(m):
            for j in range(n):
                if not lattice[i][j].get_online():
                    for x in range(r):
                        for y in range(s):
                            prio_matrix[i][j] += transformed_matrix[(i - x) % (m - r + 1)][(j - y) % (n - s + 1)]
        idx = np.argmax(prio_matrix)
        next_repair = (idx // m, idx % n)
        if lattice[next_repair[0]][next_repair[1]].get_online():
            next_repair = (-1, -1)
    else:
        found = False
        for i in range(m):
            for j in range(n):
                if not lattice[i][j].get_online():
                    next_repair = (i, j)
                    found = True
                if found:
                    break
            if found:
                break
        if not found:
            next_repair = (-1, -1)
    return np.any(transformed_matrix == (r * s)), next_repair


def simulate(m, n, r, s, end, lam, mu, smart=SMART_REPAIR):
    # Cost parameters
    cr = 0.5
    cm = 0.25
    # Initiate clock, counters, and a false failure indicator
    t = 0
    fail_flag = False
    TTF = 0
    TTF_history = []
    TBF = 0
    TBF_history = []
    total_downtime = 0
    repair_costs = 0
    maintenance_costs = 0
    repairing = False
    # Initiate queue of failures and repairs
    event_queue = PriorityQueue()
    # Create latice and fill with nodes, record planned failures
    lattice = np.empty((m, n), dtype=object)
    for i in range(m):
        for j in range(n):
            lattice[i][j] = Node()
            event_queue.put((lattice[i][j].get_time(), True, (i, j)))
            maintenance_costs += round(cm * lattice[i][j].get_time(), 6)
    # Simulation
    while t < end:
        # Get features of next event
        next_time, next_status, (i, j) = event_queue.get()
        # Update node and event queue (making event happen)
        if next_status:
            lattice[i][j].disable()
        else:
            lattice[i][j].enable(next_time)
            event_queue.put((lattice[i][j].get_time(), True, (i, j)))
            repairing = False
        # Update costs depending on node event
        if lattice[i][j].get_online():
            maintenance_costs += round(cm * lattice[i][j].get_time(), 6)
        else:
            repair_costs += cr
        # Check system status and update counters
        system_status, (x, y) = get_system_status(r, s, lattice, smart)
        if not repairing and x != -1:
            lattice[x][y].repair(next_time)
            event_queue.put((lattice[x][y].get_time(), False, (x, y)))
            repairing = True

        if system_status:
            if fail_flag:
                fail_flag = False
                TTF = 0
                total_downtime += next_time - t
                TBF += next_time - t
            else:
                TTF += next_time - t
                TBF += next_time - t
        else:
            if fail_flag:
                total_downtime += next_time - t
                TBF += next_time - t
            else:
                fail_flag = True
                TBF += next_time - t
                TBF_history.append(TBF)
                TBF = 0
                TTF += next_time - t
                TTF_history.append(TTF)
        # Advance clock
        t = min(next_time, end)
    # If the system never failed, TBF and TTF are set to the simulated time span

    if not TBF_history:
        TBF_history.append(end)
    if not TTF_history:
        TTF_history.append(end)
    return (
        total_downtime / end,
        np.mean(TTF_history),
        np.mean(TBF_history),
        repair_costs,
        maintenance_costs,
    )


def main():
    # Load Simulation Settings
    with open("qd.yaml", 'r') as f:
        config = yaml.safe_load(f)
    end = config['end']
    df = pd.DataFrame(columns=["SMART", "R", "M", "BE_PROFIT", "RELIABILITY", "MTTF", "MTBF", "AVG_R", "AVG_M"])
    for smart in [True, False]:
        for r in [2, 3, 4]:
            for m in [5, 10, 15, 30, 50]:
                reliability = []
                MTTF = []
                MTBF = []
                avg_r = []
                avg_m = []
                # m = 10
                # r = 2
                # 10000 simulation runs
                for i in range(config['runs']):
                    downtime, TTF, TBF, repair_costs, maintenance_costs = simulate(m, m, r, r, end, config['lam'], config['mu'], smart=smart)
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
                # print(breakeven_profit)
                # print(reliability)
                # print(MTTF)
                # print(MTBF)
                # print(avg_r)
                # print(avg_m)
                df.loc[len(df.index)] = [smart, r, m, breakeven_profit, reliability, MTTF, MTBF, avg_r, avg_m]
    df.to_csv("qd_data.csv", index=False)


if __name__ == "__main__":
    main()
