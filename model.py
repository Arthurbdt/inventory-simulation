import numpy as np
import pandas as pd
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

def run(length, reorder_point, order_size):
    """ Runs inventory system simulation for a given length

    Args:
        - length: length of the simulation, in months
        - reorder_point: inventory level which triggers replenishment
        - order_size: number of units to order at each replenishment
    """

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

def run_experiments(length, reorder_point_list, order_size_list, num_rep):
    """ Runs inventory simulation with every combination of reorder points and
    order sizes, and assembles results in a dataframe 
    
    Args:
        - length: length of the simulation, in months
        - reorder_point_list: list of reorder points parameters to simulate 
        - order_size_list:list of order size parameters to simulate
        - num_rep: number of replications to run for each design point 
    """
    
    # initialize results data collection
    results = []
    
    # iterate over all design points
    for i, j in itertools.product(reorder_point_list, order_size_list):
        for k in range(num_rep):
            results.append(run(length, i, j))
    
    # aggregate results into a dataframe
    results = pd.DataFrame(results)
    return results