import numpy as np
from collections import defaultdict


max_increase_wages = 0.05
max_increase_prices = 0.1
max_increase_quantity = 0.1


def merge_dict(list_dict: list[dict]) -> dict:
    """
    | Merge list of dictionaries into a single one by aggregating values into lists.

    :param list_dict: List of dictionaries to be merged.
    :return: The merged dictionary.
    """
    out_dict = defaultdict(list)
    for d in list_dict:
        for key, value in d.items():
            out_dict[key].append(value)
    return dict(out_dict)


def wages_adj() -> float:
    """
    | Helper function to generate randomness in adjusting the firm wage.

    :return: Random number.
    """
    return np.random.uniform(-max_increase_wages, max_increase_wages, 1)[0]


def price_adj() -> float:
    """
    | Helper function to generate randomness in adjusting the firm price.

    :return: Random number.
    """
    return np.random.uniform(0, max_increase_prices, 1)[0]


def supply_adj() -> float:
    """
    | Helper function to generate randomness in adjusting the firm supply.

    :return: Random number.
    """
    return np.random.uniform(0, max_increase_quantity, 1)[0]


def compute_expected_supply_price(excess_supply: float,
                                  prev_supply: float,
                                  prev_price: float,
                                  market_price: float,
                                  wage: float,
                                  productivity: float) -> tuple:
    """
    | Compute expected supply and price based on the book Macroeconomics from Bottom-up by Gatti et al. (2011)  page 55.

    :param excess_supply: Previous period excess supply.
    :param prev_supply: Previous period supply.
    :param prev_price: Previous period price.
    :param market_price: Previous period market price.
    :param wage: Current wage.
    :param productivity: Current firm productivity.
    :return: price and supply for current period.
    """
    statement_1 = (excess_supply > 0 and prev_price >= market_price)
    statement_2 = (excess_supply == 0 and prev_price < market_price)
    statement_3 = (excess_supply > 0 and prev_price < market_price)
    statement_4 = (excess_supply == 0 and prev_price >= market_price)
    if statement_1 or statement_2:  # price adjustments
        supply = prev_supply
        price = max([prev_price * (1 + price_adj() * [-1 if statement_1 else 1][0]), wage/productivity])
    else:
        price = prev_price
        supply = prev_supply * (1 + supply_adj() * [-1 if statement_3 else 1][0])
    return price, supply
