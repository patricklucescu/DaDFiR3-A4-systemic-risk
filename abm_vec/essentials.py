import numpy as np
from numpy import ndarray
from collections import defaultdict
import os
from git import Repo

max_increase_wages = 0.02
max_increase_prices = 0.02
max_increase_quantity = 0.02

RATINGS_DIST = {
    "AAA": [0.001, 0.03],
    "AA": [0.01, 0.1],
    "A": [0.02, 0.2],
    "BBB": [0.1, 0.5],
    "BB": [0.5, 2.5],
    "B": [2, 10],
}


def get_git_root_directory():
    repo = Repo(__file__, search_parent_directories=True)
    return repo.working_dir


def compute_pd(num_firms):
    """
    | Computes the probabilities of default based on credit rating distribution.

    :param num_firms: number of firms
    :return: the probabilities of default
    """
    ratings = ["AAA", "AA", "A", "BBB", "BB", "B"]
    probabilities = [0.01, 0.04, 0.15, 0.35, 0.25, 0.2]
    ratings = np.random.choice(ratings, p=probabilities, size=num_firms)
    prob_default = [
        np.random.uniform(RATINGS_DIST[rating][0], RATINGS_DIST[rating][1]) / 100
        for rating in ratings
    ]
    return prob_default


def price_adj_vectorized(size):
    """
    | Generate an array of random price adjustments.

    :param size: Number of random adjustments to generate.
    :return: Random number.
    """
    return np.random.uniform(0, max_increase_prices, size)


def supply_adj_vectorized(size):
    """
    | Generate an array of random supply adjustments.

    :param size: Number of random adjustments to generate.
    :return: Random number.
    """
    return np.random.uniform(0, max_increase_quantity, size)


def wages_adj_vectorized(size):
    """
    Generate an array of random adjustments.

    :param size: Number of random adjustments to generate.
    :return: Array of random numbers.
    """
    return np.random.uniform(-max_increase_wages, max_increase_wages, size)


def wages_adj(w_vec, min_wage):
    """
    Adjust a vector of wages with random adjustments.

    :param w_vec: Vector of wages.
    :param min_wage: Minimum wage.
    :return: Adjusted wages.
    """
    adjustment_factors = 1 + wages_adj_vectorized(len(w_vec))
    adjusted_wages = w_vec * adjustment_factors
    return np.maximum(min_wage, adjusted_wages)


def compute_expected_supply_price(
    firm_ex_supply: ndarray,
    firm_supply: ndarray,
    firm_price: ndarray,
    market_price: float,
    firm_wage: ndarray,
    firm_prod: ndarray,
    probability_excess_supply_zero: float,
    firm_profit: ndarray,
    firm_max_leverage: ndarray,
    firm_equity: ndarray,
) -> tuple:
    """

    :param firm_ex_supply: Vector of firm excess supply
    :param firm_supply: Vector of firm supply
    :param firm_price: Vector of firm prices
    :param market_price: Market price
    :param firm_wage: Vector of firm wages
    :param firm_prod: Vector of firm productivity
    :param probability_excess_supply_zero: probability_excess_supply_zero
    :param firm_profit: Vector of firm profit from previous period
    :param firm_max_leverage: Vector of firm max leverage
    :param firm_equity: Vector of firm equity
    :return:
    """

    firm_supply = firm_supply * (1 + firm_profit)

    statement_1 = (firm_ex_supply > 0) & (firm_price >= market_price)  # decrease price
    statement_2 = (firm_ex_supply == 0) & (firm_price < market_price)  # incerease price
    statement_3 = (firm_ex_supply > 0) & (firm_price < market_price)  # decrease supply
    # statement_4 = (firm_ex_supply == 0) & (firm_price >= market_price) #increase supply

    # price and supply adjustment factor
    prc_excess_supply_factor = np.where(
        statement_1,
        -probability_excess_supply_zero / (1 - probability_excess_supply_zero),
        1,
    )
    sup_excess_supply_factor = np.where(
        statement_3,
        -probability_excess_supply_zero / (1 - probability_excess_supply_zero),
        1,
    )

    price_adj = price_adj_vectorized(len(firm_price))
    supply_adj = supply_adj_vectorized(len(firm_price))

    firm_price = np.where(
        statement_1 | statement_2,
        firm_price * (1 + price_adj * prc_excess_supply_factor),
        firm_price,
    )
    firm_supply = np.where(
        ~(statement_1 | statement_2),
        firm_supply * (1 + supply_adj * sup_excess_supply_factor),
        firm_supply,
    )

    # make sure firm does not go beyond max leverage
    supply_threshold = firm_prod * (1 + firm_max_leverage) * firm_equity / firm_wage
    supply_threshold_breach = np.sum(firm_supply > supply_threshold)
    firm_supply = np.minimum(firm_supply, supply_threshold)
    firm_total_wage = firm_wage * firm_supply / firm_prod

    # adjust minimum price
    firm_price = np.where(
        statement_1 | statement_2,
        np.maximum(
            firm_price,
            firm_wage / firm_prod
            + np.maximum(0, firm_total_wage - firm_equity) / firm_supply,
        ),
        firm_price,
    )
    # adjust price so you get a minimum price to cover costs

    return firm_price, firm_supply, firm_total_wage, supply_threshold_breach
