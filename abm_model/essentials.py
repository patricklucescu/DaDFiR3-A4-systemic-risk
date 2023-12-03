import numpy as np
from collections import defaultdict
import os
from git import Repo

max_increase_wages = 0.02
max_increase_prices = 0.02
max_increase_quantity = 0.02

RATINGS_DIST = {
    'AAA': [0.001, 0.03],
    'AA': [0.01, 0.1],
    'A': [0.02, 0.2],
    'BBB': [0.1, 0.5],
    'BB': [0.5, 2.5],
    'B': [2, 10]
}


def get_git_root_directory():
    repo = Repo(__file__, search_parent_directories=True)
    return repo.working_dir


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


def compute_pd(num_firms):
    """
    | Computes the probabilities of default based on credit rating distribution.

    :param num_firms: number of firms
    :return: the probabilities of default
    """
    ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B']
    probabilities = [0.01, 0.04, 0.15, 0.35, 0.25, 0.2]
    ratings = np.random.choice(ratings, p=probabilities, size=num_firms)
    prob_default = [np.random.uniform(RATINGS_DIST[rating][0],RATINGS_DIST[rating][1]) / 100 for rating in ratings]
    return prob_default


def compute_expected_supply_price(excess_supply: float,
                                  prev_supply: float,
                                  prev_price: float,
                                  market_price: float,
                                  wage: float,
                                  productivity: float,
                                  probability_excess_supply_zero: float,
                                  profit: float) -> tuple:
    """
    | Compute expected supply and price based on the book Macroeconomics from Bottom-up by Gatti et al. (2011)  page 55.

    :param excess_supply: Previous period excess supply.
    :param prev_supply: Previous period supply.
    :param prev_price: Previous period price.
    :param market_price: Previous period market price.
    :param wage: Current wage.
    :param productivity: Current firm productivity.
    :param probability_excess_supply_zero from markov model
    :param profit: last period's profit in %
    :return: price and supply for current period.

    """
    statement_1 = (excess_supply > 0 and prev_price >= market_price)
    statement_2 = (excess_supply == 0 and prev_price < market_price)
    statement_3 = (excess_supply > 0 and prev_price < market_price)
    statement_4 = (excess_supply == 0 and prev_price >= market_price)

    prev_supply = prev_supply * (1+profit)

    if statement_1 or statement_2:  # price adjustments
        supply = prev_supply
        price = max([prev_price * (1 + price_adj() * [-probability_excess_supply_zero/(1-probability_excess_supply_zero)
                                                      if statement_1 else 1][0]), 0.0 * wage/productivity])
    else:
        price = prev_price
        supply = prev_supply * (1 + supply_adj() * [-probability_excess_supply_zero/(1-probability_excess_supply_zero) if statement_3 else 1][0])

    return price, supply
