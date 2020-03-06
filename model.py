import numpy as np
import simpy
import itertools

# demand variables
demand_sizes = [1, 2, 3, 4]
demand_prob = [1/6, 1/3, 1/3, 1/6]
start_inventory = 60.

# costs variables
order_cost_setup = 32.
order_cost_per_item = 3.
monthly_backlog_cost_per_item = 5.
monthly_holding_cost_per_item = 1.

mean_interdemand_time = .1      # exponentially distributed

class InventorySystem():
    """ Monitors inventory level and ordering, shortage and holding costs """

    def __init__(self, env, reorder_point, order_size):
        
        # input variables
        self.reorder_point = reorder_point
        self.order_size = order_size
        self.level = start_inventory
        self.last_change = 0.

        # initialize performance measures
        self.ordering_cost = 0.
        self.shortage_cost = 0.
        self.holding_cost = 0.


def check_inventory(env, inventory):
    """ Checks inventory at regular interval and places order if needed """

    while True:
        # check inventory
        if inventory.level < inventory.reorder_point:
            units_ordered = (inventory.order_size + 
                             inventory.reorder_point - inventory.level)
            env.process(place_order(env, inventory, units_ordered))

        # wait for until next inventory check
        yield env.timeout(1.0)

def place_order(env, inventory, units_ordered):
    """ Places order and updates inventory level when order has been 
    received """

    # update ordering cost
    inventory.ordering_cost += (order_cost_setup + order_cost_per_item * 
                                units_ordered)

    # wait for next order to arrive
    delivery_delay = np.random.uniform(.5, 1.0)
    yield env.timeout(delivery_delay)

    # update inventory level and compute costs
    update_costs(inventory, env.now)
    inventory.level += units_ordered
    inventory.last_change = env.now

def update_costs(inventory, date):
    """ Computes shortage and holding costs before each change in 
    inventory """

    # check for shortage
    if inventory.level <= 0:
        period_shortage_cost = (abs(inventory.level) * 
                                monthly_backlog_cost_per_item * 
                                (date -  inventory.last_change))
        inventory.shortage_cost += period_shortage_cost
        
    # compute holding costs
    else:
        period_holding_cost = (inventory.level * 
            monthly_holding_cost_per_item * 
            (date -  inventory.last_change))
        inventory.holding_cost += period_holding_cost

def demand(env, inventory):
    """ Generates demand at random intervals and updates inventory level """

    while True:
        # create demand at random interval
        iat = np.random.exponential(mean_interdemand_time)
        size = np.random.choice(demand_sizes, 1, p=demand_prob)
        yield env.timeout(iat)

        # decrease inventory levels and update costs
        update_costs(inventory, env.now)
        inventory.level -= size[0]
        inventory.last_change = env.now

def run(length:float, reorder_point:float, order_size:float):
    """ Runs inventory system simulation for a given length

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
    inventory = InventorySystem(env, reorder_point, order_size)
    env.process(check_inventory(env, inventory))
    env.process(demand(env, inventory))
    env.run(length)

    # compute and return simulation results
    avg_total_cost = (inventory.ordering_cost + inventory.holding_cost + 
                      inventory.shortage_cost) / length
    avg_ordering_cost = inventory.ordering_cost / length
    avg_holding_cost = inventory.holding_cost / length
    avg_shortage_cost = inventory.shortage_cost / length

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
    if (isinstance(reorder_points, list) == False) or (isinstance(
            order_sizes, list) == False):
        raise TypeError('Reorder points and order sizes must be lists')
    
    if length <= 0:
        raise ValueError("Simulation length must be greater than zero")
    
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
