import numpy as np
from queue import PriorityQueue
import math
import yaml
import importlib
import sys
import os
import matplotlib.pyplot as plt
import csv
class Node:
    def __init__(self, lam= 10, mu=10):
        # Uptime rate (lam) and downtime rate (mu); they give average periods until event
        self.__status = True
        self.__next_event = np.random.exponential(lam)
        self.__lam = lam
        self.__mu = mu

    def update(self, event, current_time):
        # Boolean event decides if uptime or downtime computed; setter for status and next event
        if event:
            self.__status = True
            self.__next_event = current_time + np.random.exponential(self.__lam)
        else:
            self.__status = False
            self.__next_event = current_time + np.random.exponential(self.__mu)

    def getStatus(self):
        return self.__status

    def getNext(self):
        return self.__next_event


def check_system(r, s, lattice):
    m = len(lattice)
    n = len(lattice[0])
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
        #Build intersection of the r rows
        init_set = set(transformed_matrix[row % m])
        for more in range(r):
            init_set = init_set & set(transformed_matrix[(row + more) % m])
        if (init_set):
                return 0
    return 1


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
        system_status = check_system(r, s, lattice)
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
    END = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300]
    total_breakeven_profit = []
    total_reliability = []
    total_MTTF = []
    total_MTBF = []
    total_avg_r = []
    total_avg_m = []
    for i in range(len(END)):
        end = END[i]
        reliability = []
        MTTF = []
        MTBF = []
        avg_r = []
        avg_m = []
        print("END = %d" %end)
        # 10000 simulation runs
        for j in range(100):
            downtime, TTF, TBF, repair_costs, maintenance_costs = simulate(6, 6, 3, 3, end, 5, 2)
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
        total_breakeven_profit.append(breakeven_profit)
        total_reliability.append(reliability)
        total_MTTF.append(MTTF)
        total_MTBF.append(MTBF)
        total_avg_r.append(avg_r)
        total_avg_m.append(avg_m)
        print(breakeven_profit)
        print(reliability)
        print(MTTF)
        print(MTBF)
        print(avg_r)
        print(avg_m)


    with open('reliability_analysis/extensions/diffSpan/output.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["lifetime","breakeven profit","reliability","MTTF","MTBF","avg_r","avg_m"])
        for i in range(len(END)):
            writer.writerow([END[i],total_breakeven_profit[i],total_reliability[i],total_MTTF[i],total_MTBF[i],total_avg_r[i],total_avg_m[i]])

            
    plot1 = plt.plot(END, total_breakeven_profit)
    plt.xlabel('System Time Span'); plt.ylabel('breakeven_profit')
    plt.show()
    plot2 = plt.plot(END, total_reliability)
    plt.xlabel('System Time Span'); plt.ylabel('reliability')
    plt.show()
    plot3 = plt.plot(END, total_MTTF)
    plt.xlabel('System Time Span'); plt.ylabel('MTTF')
    plt.show()
    plot4 = plt.plot(END, total_MTBF)
    plt.xlabel('System Time Span'); plt.ylabel('MTBF')
    plt.show()
    plot5 = plt.plot(END, total_avg_r)
    plt.xlabel('System Time Span'); plt.ylabel('avg_r')
    plt.show()
    plot6 = plt.plot(END, total_avg_m)
    plt.xlabel('System Time Span'); plt.ylabel('avg_m')
    plt.show()

if __name__ == "__main__":
    main()
