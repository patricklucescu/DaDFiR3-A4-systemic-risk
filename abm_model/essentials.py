import numpy as np
from collections import defaultdict


max_increase_wages = 0.05
max_increase_prices = 0.1
max_increase_quantity = 0.1


def merge_dict(list_dict):
    """Merge list of dictionaries into a single one by aggregating values into lists."""
    out_dict = defaultdict(list)
    for d in list_dict:
        for key, value in d.items():
            out_dict[key].append(value)
    return dict(out_dict)

def wages_adj():
    return np.random.uniform(0, max_increase_wages, 1)


def price_adj():
    return np.random.uniform(0, max_increase_prices, 1)


def supply_adj():
    return np.random.uniform(0, max_increase_quantity, 1)



