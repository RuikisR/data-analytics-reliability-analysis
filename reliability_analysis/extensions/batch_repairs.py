def simulate(m, n, r, s, end, B):
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
    standby_list = []
    # Create latice and fill with nodes, record planned failures
    lattice = np.empty((m, n), dtype=object)
    for i in range(m):
        for j in range(n):
            lattice[i][j] = Node()
            event_queue.put((lattice[i][j].getNext(), True, m * i + j))
            maintenance_costs += round(cm * lattice[i][j].getNext(), 6)
    # Simulation
    while (t < end):
        # Get features of next event
        next_event = event_queue.get()
        next_time = next_event[0]
        next_status = next_event[1]
        next_node = next_event[2]
        i = int(next_node / m)
        j = next_node % n
        # Update node and event queue (making event happen), incur costs
        # False status means it's about to get repaired; execute batch operation
        if next_status == False:
            standby_list.append([i,j])
            if len(standby_list) == B:
                repair_costs += cr
                for x, y in standby_list:
                    lattice[x][y].update(True, next_time)
                    event_queue.put((lattice[x][y].getNext(), lattice[x][y].getStatus(), m * x + y))
                    maintenance_costs += round(cm * lattice[x][y].getNext(), 6)
                standby_list.clear()
            # Not repairing if batch not full
        else:
            # True status means it's about to break, update lattice normally
            lattice[i][j].update(False, next_time)
            event_queue.put((lattice[i][j].getNext(), lattice[i][j].getStatus(), m * i + j))
        # Check system status and update counters
        system_status = check_system(r, s, lattice)
        if system_status == 0 and TTF == end:
            TTF = next_time
        if system_status == 0:
            if fail_flag:
                total_downtime += (next_time - t)
            else:
                TBF += (next_time - t)
                TBF_history.append(TBF)
                fail_flag = 1
                TBF = 0
        else:
            if fail_flag:
                total_downtime += (next_time - t)
                fail_flag = 0
            else:
                TBF += (next_time - t)
        # Advance clock
        t = min(next_time, end)
    # If the system never failed, TBF and TTF are set to the simulated time span
    if not TBF_history:
        TBF_history.append(end)
    return total_downtime / end, TTF, np.mean(TBF_history), repair_costs, maintenance_costs

def main():
    # Number of periods to simulate and metrics
    end = 30
    B_set = range(1,10,1)
    reliability_set = []
    MTTF_set = []
    MTBF_set = []
    avg_r_set = []
    avg_m_set = []
    breakeven_set = []
    for B in B_set:
        reliability = []
        MTTF = []
        MTBF = []
        avg_r = []
        avg_m = []
        # 10000 simulation runs
        tic = time.time()
        for i in range(100):
            toc = time.time()
            downtime, TTF, TBF, repair_costs, maintenance_costs = simulate(6, 6, 3, 3, end, B)
            reliability.append(downtime)
            MTTF.append(TTF)
            MTBF.append(TBF)
            avg_r.append(repair_costs)
            avg_m.append(maintenance_costs)
        reliability = 1 - np.mean(reliability)
        print(reliability)
        MTTF = np.mean(MTTF)
        MTBF = np.mean(MTBF)
        avg_r = round(np.mean(avg_r), 6)
        avg_m = round(np.mean(avg_m), 6)
        breakeven_profit = round((avg_r + avg_m) / (reliability * end), 6)
        breakeven_set.append(breakeven_profit)
        reliability_set.append(reliability)
        MTTF_set.append(MTTF)
        MTBF_set.append(MTBF)
        avg_r_set.append(avg_r)
        avg_m_set.append(avg_m)
        #print(reliability_set)
        #print(avg_r)
    #Cost plot
    fig, ax = plt.subplots()
    ax.set_xlabel('batch size')
    ax.set_ylabel('Euro (millions)')
    ax.plot(B_set, breakeven_set, color = 'green', linewidth = 2, label = 'breakeven profit')
    ax.plot(B_set, avg_m_set, color = 'red', linewidth = 2, label = 'maintenance cost')
    ax.plot(B_set, avg_r_set, color = 'blue', linewidth = 2, label = 'repair cost')
    ax.legend(loc='upper left', title='Metric', bbox_to_anchor=(1, 1.02))

    #Failure time plot
    fig, ax = plt.subplots()
    ax.set_xlabel('batch size')
    ax.set_ylabel('Time (years)')
    ax.plot(B_set, MTTF_set, color = 'red', linewidth = 2, label = 'MTTF')
    ax.plot(B_set, MTBF_set, color = 'blue', linewidth = 2, label = 'MTBF')
    ax.legend(loc='upper left', title='Metric', bbox_to_anchor=(1, 1.02))

    #Reliability plot
    fig, ax = plt.subplots()
    ax.set_xlabel('batch size')
    ax.set_ylabel('Reliability')
    ax.plot(B_set, reliability_set, color='green', linewidth=2)

    plt.show()
