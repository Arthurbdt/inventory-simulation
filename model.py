import numpy as np
import simpy
import itertools

# simulation variables
mean_iat = .1                       # average time between customer demands (months)
demand_sizes = [1, 2, 3, 4]         # possible customer demand sizes
demand_prob = [1/6, 1/3, 1/3, 1/6]  # probability of each demand size
start_inventory = 60.               # units in inventory at simulation start
order_cost_setup = 32.
order_cost_per_item = 3.
backlog_cost_per_item = 5.
holding_cost_per_item = 1.

class InventorySystem:
    """ Single product inventory system using a fixed reorder point
    and order size policy. Inventory is reviewed at regular intervals """

    def __init__(self, env, reorder_point, order_size):
        # initialize values
        self.reorder_point = reorder_point
        self.order_size = order_size
        self.level = start_inventory
        self.last_change = 0.
        self.ordering_cost = 0.
        self.shortage_cost = 0.
        self.holding_cost = 0.
        # launch processes
        env.process(self.review_inventory(env))
        env.process(self.demands(env))

    def place_order(self, env, units):
        """ Place and receive orders """
        # update ordering costs
        self.ordering_cost += (order_cost_setup
                              + units * order_cost_per_item)
        # determine when order will be received
        lead_time = np.random.uniform(.5, 1.0)
        yield env.timeout(lead_time)
        # update inventory level and costs
        self.update_cost(env)
        self.level += units
        self.last_change = env.now
    
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
                                * backlog_cost_per_item
                                * (env.now - self.last_change))
            self.shortage_cost += shortage_cost
        else:
            # update holding cost
            holding_cost = (self.level
                            * holding_cost_per_item
                            * (env.now - self.last_change))
            self.holding_cost += holding_cost
    
    def demands(self, env):
        """ Generate demand at random intervals and update
         inventory level """
        while True:
            # generate next demand size and time
            iat = np.random.exponential(mean_iat)
            size = np.random.choice(demand_sizes, 1, p=demand_prob)
            yield env.timeout(iat)
            # update inventory level and costs upon demand receipt
            self.update_cost(env)
            self.level -= size[0]
            self.last_change = env.now

def run(length:float, reorder_point:float, order_size:float):
    """ Runs inventory system simulation for a given length and returns
    simulation results in a dictionary

    Args:
        - length: length of the simulation, in months
        - reorder_point: inventory level which triggers replenishment
        - order_size: number of units to order at each replenishment
    """
    # check user inputs
    if length <= 0:
        raise ValueError("Simulation length must be greater than zero")
    if order_size < 0:
        raise ValueError("Order size must be greater than zero")  
    # setup simulation
    env = simpy.Environment()
    inv = InventorySystem(env, reorder_point, order_size)
    env.run(length)
      # compute and return simulation results
    avg_total_cost = (inv.ordering_cost 
                    + inv.holding_cost 
                    + inv.shortage_cost) / length
    avg_ordering_cost = inv.ordering_cost / length
    avg_holding_cost = inv.holding_cost / length
    avg_shortage_cost = inv.shortage_cost / length
    results = {'reorder_point': reorder_point,
               'order_size': order_size,
               'total_cost': round(avg_total_cost, 1), 
               'ordering_cost': round(avg_ordering_cost, 1),
               'holding_cost': round(avg_holding_cost, 1), 
               'shortage_cost': round(avg_shortage_cost, 1)}      
    return results

def run_experiments(length, reorder_points, order_sizes, num_rep):
    """ Runs inventory simulation with every combination of reorder points and
    order sizes, and assembles results in a list of dictionaries
    
    Args:
        - length: length of the simulation, in months
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
            results.append(run(length, i, j))
    return results