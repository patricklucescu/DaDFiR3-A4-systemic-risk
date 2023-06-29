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


def compute_expected_supply_price(excess_supply, prev_supply, prev_price, market_price):
    statement_1 = (excess_supply > 0 and prev_price >= market_price)
    statement_2 = (excess_supply == 0 and prev_price < market_price)
    statement_3 = (excess_supply > 0 and prev_price < market_price)
    statement_4 = (excess_supply == 0 and prev_price >= market_price)
    if statement_1 or statement_2:  # price adjustments
        supply = prev_supply
        price = prev_price * (1 + price_adj()[0] * [-1 if statement_1 else 1][0])
    else:
        price = prev_price
        supply = prev_supply * (1 + supply_adj()[0] * [-1 if statement_1 else 1][0])
    return price, supply
