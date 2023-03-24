import numpy as np


class Node:
    print("Overrided Node class from template extension")
    def __init__(self, lam=10, mu=10):
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