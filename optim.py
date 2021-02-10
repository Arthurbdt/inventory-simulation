import model
import numpy as np
import random
import matplotlib.pyplot as plt

xbounds = [0, 100]  # extreme values for reorder point
ybounds = [5, 100]  # extreme values for order size

class LocalSearch:
    """ Greedy algorithm exploring neighboring solutions and 
    only selecting better neighbors """

    def __init__(self, start, n, runs):
        # compute initial value
        self.path = []
        self.cost = []
        val = [model.run(120, start[0], start[1])['total_cost'] for j in range(runs)]
        best = np.mean(val)
        self.path = start
        self.cost.append(best)

        # complete n steps search
        for i in range(1,n):
            next = self.neighbor(start)
            val = [model.run(120, next[0], next[1])['total_cost'] for j in range(runs)]
            val = np.mean(val)
            # only select neighbor if solution improves 
            if val < best:
                best = val
                self.path = np.vstack([self.path, next])
                self.cost.append(val)
                start = next
       
    def neighbor(self, start):
        """ Create new neighbor within acceptable bounds """
        x = start[0] + random.uniform(-20, 20)
        y = start[1] + random.uniform(-20, 20)
        x = max(min(x, xbounds[1]), xbounds[0])
        y = max(min(y, ybounds[1]), ybounds[0])
        return [x,y]
