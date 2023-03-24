import numpy as np
from queue import PriorityQueue
import math

# Uptime rate (lam) and downtime rate (mu); they give average periods until event
lam = 10
mu = 10

class Node:
    def __init__(self):
        self.__status = True
        self.__next_event = np.random.exponential(lam)

    def update(self, event, current_time):
        #Boolean event decides if uptime or downtime computed; setter for status and next event
        if event:
            self.__status = True
            self.__next_event = current_time + np.random.exponential(lam)
        else:
            self.__status = False
            self.__next_event = current_time + np.random.exponential(mu)

    def getStatus(self):
        return self.__status

    def getNext(self):
        return self.__next_event

def check_system(r, s, lattice):
    m = len(lattice)
    n = len(lattice[0])
    #Building transformed matrix
    transformed_matrix = []
    flag = 0
    for i in range(m):
        transformed_row = []
        for j in range(n + s - 1):
            #Scan the lattice for dangerous rows, hopping over columns' end
            if not lattice[i % m][j % n].getStatus():
                flag += 1
                if flag == s:
                    transformed_row.append((j-s+1) % n)
                    flag -= 1
            else:
                flag = 0
        transformed_matrix.append(transformed_row)
    #Scan transformed matrix to see if it's broken
    for row in range(m + r - 1):
        if (set(transformed_matrix[row % m]) & set(transformed_matrix[(row + 1) % m])):
            return 0
    return 1

def simulate(m, n, r, s):
    # Simulation end
    end = 50
    # Initiate queue of failures and repairs
    event_queue = PriorityQueue()
    # Create latice and fill with nodes, record initial failures
    lattice = np.empty((m, n), dtype=object)
    for i in range(m):
        for j in range(n):
            lattice[i][j] = Node()
            event_queue.put((lattice[i][j].getNext(), True, m * i + j))
    # Initiate system status history
    t = 0
    system_history = []
    # Simulation
    while (t < end):
        # Get features of next event
        next_event = event_queue.get()
        next_time = next_event[0]
        next_status = next_event[1]
        next_node = next_event[2]
        i = int(next_node / m)
        j = next_node % n
        # If it's a new period, all nodes of previous one are updated
        # and system check commences before new updates
        if (t != math.ceil(next_time)):
            system_status = check_system(r, s, lattice)
            # Fill in system status for each period without events
            for k in range(min(math.ceil(next_time), end) - t):
                system_history.append(system_status)
        # Advance clock
        t = min(math.ceil(next_time), end)
        # Update node and event queue
        lattice[i][j].update(not next_status, t)
        event_queue.put((lattice[i][j].getNext(), lattice[i][j].getStatus(), m * i + j))
    return system_history

def main():
    system_history = simulate(3, 3, 2, 2)
    return system_history

if __name__ == "__main__":
    system_history = main()
    print(system_history)
    print(len(system_history))
