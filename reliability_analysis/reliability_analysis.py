import numpy as np
from queue import PriorityQueue
import math

# Uptime rate (lam) and downtime rate (mu); they give average periods until event
lam = 10
mu = 10
# Simulation end
end = 50
# Lattice dimensions
m = 3
n = 3
r = 2
s = 2


class Node:
    def __init__(self):
        self.__status = True
        self.__next_event = np.random.exponential(lam)

    def update(self, event, current_time):
        # Boolean event decides if uptime or downtime computed; setter for status and next event
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


def main():
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
    while t < end:
        # Get features of next event
        next_event = event_queue.get()
        next_time, next_status, next_node = next_event
        i = next_node // m
        j = next_node % n
        # Advance clock
        t = min(end, math.ceil(next_time))
        # Update node and event queue
        lattice[i][j].update(not next_status, t)
        event_queue.put((lattice[i][j].getNext(), lattice[i][j].getStatus(), m * i + j))
        # TODO: Check system integrity
        system_history.append(t)
    return system_history


if __name__ == "__main__":
    system_history = main()
    print(system_history)
