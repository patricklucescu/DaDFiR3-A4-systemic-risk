import numpy as np
from numpy import ndarray

from abm_vec.essentials.market_adjustments import (
    price_adj_vectorized,
    supply_adj_vectorized,
)


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
    policy_rate: float,
) -> tuple[ndarray, ndarray, ndarray, int, float]:
    """
    | Dynamically computes the expected supply and price for firms in a market-based simulation. It adjusts firm supply
    and price based on several factors including market price, firm productivity, and leverage limits.

    | This function performs several key operations:

    #. Adjusts firm supply based on the profit from the previous period.

    #. Identify four different scenarios based on the firm's excess supply and price relative to the market price:
        * In scenario 1, the firm has excess supply and the price is greater than or equal to the market price. In this
            case, the firm decreases its price.
        * In scenario 2, the firm has no excess supply and the price is less than the market price. In this case, the
            firm increases its price.
        * In scenario 3, the firm has excess supply and the price is less than the market price. In this case, the
            firm decreases its supply.

        * In scenario 4, the firm has no excess supply and the price is greater than or equal to the market price. In
            this case, the firm increases its supply.

    #. Ensures that firms do not exceed their maximum leverage.

    #. Adjusts firm prices to cover the minimum costs.

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
    :param policy_rate: Policy rate
    :return:
    """

    # adjust supply based on profit
    firm_supply = firm_supply * (1 + firm_profit)
    # generate scenarios
    statement_1 = (firm_ex_supply > 0) & (firm_price >= market_price)  # decrease price
    statement_2 = (firm_ex_supply == 0) & (firm_price < market_price)  # increase price
    statement_3 = (firm_ex_supply > 0) & (firm_price < market_price)  # decrease supply
    # statement_4 = (firm_ex_supply == 0) & (firm_price >= market_price) # increase supply

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
    min_price = (
        firm_wage / firm_prod
        + policy_rate * np.maximum(0, firm_total_wage - firm_equity) / firm_supply
    )
    # count number of min price breaches
    min_price_breach = np.sum(
        (min_price > firm_price) & (statement_1 | statement_2)
    ) / np.sum((statement_1 | statement_2))

    firm_price = np.where(
        statement_1 | statement_2, np.maximum(firm_price, min_price), firm_price
    )

    return firm_price, firm_supply, firm_total_wage, supply_threshold_breach, min_price_breach
