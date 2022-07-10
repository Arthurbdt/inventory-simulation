import numpy as np
import simpy
import itertools
import matplotlib.pyplot as plt

# simulation constants
MEAN_IAT = .1                       # average time between customer demands (months)
DEMAND_SIZES = [1, 2, 3, 4]         # possible customer demand sizes
DEMAND_PROB = [1/6, 1/3, 1/3, 1/6]  # probability of each demand size
START_INVENTORY = 60.               # units in inventory at simulation start
COST_ORDER_SETUP = 32.              # fixed cost of placing an order
COST_ORDER_PER_ITEM = 3.            # variable cost of ordering an item
COST_BACKLOG_PER_ITEM = 5.          # monthly cost for each item in backlog
COST_HOLDING_PER_ITEM = 1.          # monthly cost for each item in inventory
SIM_LENGTH = 120.                   # duration of the simulation (in months)

class InventorySystem:
    """ Single product inventory system using a fixed reorder point
    and order size policy. Inventory is reviewed at regular intervals """

    def __init__(self, env, reorder_point, order_size):
        # initialize values
        self.reorder_point = reorder_point
        self.order_size = order_size
        self.level = START_INVENTORY
        self.last_change = 0.
        self.ordering_cost = 0.
        self.shortage_cost = 0.
        self.holding_cost = 0.
        self.history = [(0., START_INVENTORY)]
        # launch processes
        env.process(self.review_inventory(env))
        env.process(self.demands(env))

    def place_order(self, env, units):
        """ Place and receive orders """
        # update ordering costs
        self.ordering_cost += (COST_ORDER_SETUP
                              + units * COST_ORDER_PER_ITEM)
        # determine when order will be received
        lead_time = np.random.uniform(.5, 1.0)
        yield env.timeout(lead_time)
        # update inventory level and costs
        self.update_cost(env)
        self.level += units
        self.last_change = env.now
        self.history.append((env.now, self.level))
    
    def review_inventory(self, env):
        """ Check inventory level at regular intervals and place
        orders inventory level is below reorder point """
        while True:
            # place order if required
            if self.level <= self.reorder_point:
                units = (self.order_size
                        + self.reorder_point
                        - self.level)
                env.process(self.place_order(env, units))
            # wait for next check
            yield env.timeout(1.0)

    def update_cost(self, env):
        """ Update holding and shortage cost at each inventory
         movement """
        # update shortage cost
        if self.level <= 0:
            shortage_cost = (abs(self.level)
                                * COST_BACKLOG_PER_ITEM
                                * (env.now - self.last_change))
            self.shortage_cost += shortage_cost
        else:
            # update holding cost
            holding_cost = (self.level
                            * COST_HOLDING_PER_ITEM
                            * (env.now - self.last_change))
            self.holding_cost += holding_cost
    
    def demands(self, env):
        """ Generate demand at random intervals and update
         inventory level """
        while True:
            # generate next demand size and time
            iat = np.random.exponential(MEAN_IAT)
            size = np.random.choice(DEMAND_SIZES, 1, p=DEMAND_PROB)
            yield env.timeout(iat)
            # update inventory level and costs upon demand receipt
            self.update_cost(env)
            self.level -= size[0]
            self.last_change = env.now
            self.history.append((env.now, self.level))

def run(reorder_point:float, order_size:float, display_chart = False):
    """ Runs inventory system simulation for a given length and returns
    simulation results in a dictionary

    Args:
        - length: length of the simulation, in months
        - reorder_point: inventory level which triggers replenishment
        - order_size: number of units to order at each replenishment
    """
    # check user inputs
    if SIM_LENGTH <= 0:
        raise ValueError("Simulation length must be greater than zero")
    if order_size < 0:
        raise ValueError("Order size must be greater than zero")  
    # setup simulation
    env = simpy.Environment()
    inv = InventorySystem(env, reorder_point, order_size)
    env.run(SIM_LENGTH)
      # compute and return simulation results
    avg_total_cost = (inv.ordering_cost 
                    + inv.holding_cost 
                    + inv.shortage_cost) / SIM_LENGTH
    avg_ordering_cost = inv.ordering_cost / SIM_LENGTH
    avg_holding_cost = inv.holding_cost / SIM_LENGTH
    avg_shortage_cost = inv.shortage_cost / SIM_LENGTH
    results = {'reorder_point': reorder_point,
               'order_size': order_size,
               'total_cost': round(avg_total_cost, 1), 
               'ordering_cost': round(avg_ordering_cost, 1),
               'holding_cost': round(avg_holding_cost, 1), 
               'shortage_cost': round(avg_shortage_cost, 1)}
    if display_chart == True:
        step_graph(inv)    
    return results

def step_graph(inventory):
    """ Displays a step line chart of inventory level """
    # create subplot
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.grid(which = 'major', alpha = .4)
    # plot simulation data
    x_val = [x[0] for x in inventory.history]
    y_val = [x[1] for x in inventory.history]
    plt.step(x_val, y_val, where = 'post', label='Units in inventory')
    plt.axhline(y=0, color='red', linestyle='-', label='Shortage threshold') 
    plt.axhline(y=inventory.reorder_point, color='green', linestyle='--', label='Reorder point')  # reorder point line
    # titles and legends
    plt.xlabel('Months')
    plt.ylabel('Units in inventory')
    plt.title(f'Simulation output for system ({inventory.reorder_point}, {inventory.order_size})')
    plt.gca().legend()
    plt.show()

def run_experiments(reorder_points, order_sizes, num_rep):
    """ Runs inventory simulation with every combination of reorder points and
    order sizes, and assembles results in a list of dictionaries
    
    Args:
        - reorder_points: list of reorder points parameters to simulate 
        - order_sizes:list of order size parameters to simulate
        - num_rep: number of replications to run for each design point 
    """   
    # validate user inputs:   
    if num_rep <=0:
        raise ValueError('Number of replications must be greater than zero') 
    # initiate variables
    len1 = len(reorder_points)
    len2 = len(order_sizes)
    iter_count = 0
    results = [] 
    # iterate over all design points
    for i, j in itertools.product(reorder_points, order_sizes):
        for k in range(num_rep):
            iter_count += 1
            # display a message to user every 100 replications
            if iter_count % 100 == 0:
                print('Iteration', iter_count, 'of', len1 * len2 * num_rep)
            # record results
            results.append(run(i, j))
    return results

# run simulation
if __name__ == '__main__':
    print(run(25,40))