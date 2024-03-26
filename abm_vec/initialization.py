import os
import random

import numpy as np
import pandas as pd
from numpy import ndarray

from abm_vec.essentials.default_probability import compute_pd
from abm_vec.essentials.distributions import bounded_pareto_normal
from abm_vec.essentials.util import get_git_root_directory


def get_bank_data() -> dict[str, np.ndarray]:
    """
    | Loads the bank data retried from Fitch Connect and returns it as a dictionary.

    :return: dictionary with bank data as vectors.
    """
    bank_df: pd.DataFrame = pd.read_excel(
        os.path.join(get_git_root_directory(), "data/banks-swiss.xlsx")
    )
    bank_df = bank_df.loc[
        (bank_df["Total Deposits"] != "-")
        & (bank_df["Gross Loans"] != "-")
        & (bank_df["Total Corp. Loans"] != "-"),
        :,
    ]
    # bank_df = bank_df.iloc[1:, :]
    bank_df.reset_index(inplace=True, drop=True)
    # Equity, Deposits, and Loans need to be multiplied by 10^6 as they are reported
    # in millions of CHF
    return {
        "equity": bank_df["Total Equity"].values * 10**6,
        "deposits": bank_df["Total Deposits"].values * 10**6,
        "loans": bank_df["Total Corp. Loans"].values * 10**6,
        "t1_cap": bank_df["Tier 1 Cap. Ratio"].values,
    }


def generate_random_entities(calibration_variables: dict) -> tuple:
    """
    | Generate random firms based on the model parameters.
    | The generation of firm characteristics is as follows:

    * The firm productivity is :math:`\alpha` is assumed to be constant across firms.

    * The firm excess supply is drawn from a Bernoulli distribution with a certain probability.

    * The firm wage is the minimum wage plus a random adjustment.

    * The firm maximum leverage is drawn from a uniform distribution.

    * The firm price is the market price plus a random adjustment.

    * The firm equity and supply are drawn from a join distribution with bounded pareto marginals and normal copula.

    * The firm profit is set to zero.

    * The firm probability of default is computed based on the firm maximum leverage and the calibration parameter.

    :param calibration_variables: Dictionary containing all calibration settings from calibration.py
    :return: A tuple containing the generated firms & banks vectors of info.
    """

    firm_prod = np.array(
        [calibration_variables["min_productivity"]] * calibration_variables["FIRMS"]
    )
    firm_ex_supply = np.array(
        [
            x
            for x in np.random.binomial(
                1,
                calibration_variables["firm_init_excess_supply_prob"],
                calibration_variables["FIRMS"],
            )
        ]
    )
    firm_wage = np.array(
        [
            calibration_variables["min_wage"]
            + abs(
                np.random.normal(
                    calibration_variables["min_wage"] * 0.05,
                    (calibration_variables["min_wage"] * 0.1) ** 0.5,
                )
            )
            for x in range(calibration_variables["FIRMS"])
        ]
    )
    firm_max_leverage = np.array(
        [
            random.randint(
                calibration_variables["min_max_leverage"],
                calibration_variables["max_max_leverage"],
            )
            for i in range(calibration_variables["FIRMS"])
        ]
    )
    firm_pd = (
        calibration_variables["leverage_severity"]
        * (1 + firm_max_leverage - calibration_variables["min_max_leverage"])
        / (
            1
            + calibration_variables["max_max_leverage"]
            - calibration_variables["min_max_leverage"]
        )
    )

    firm_equity, firm_supply = bounded_pareto_normal(
        calibration_variables["FIRMS"],
        calibration_variables["firm_lb1"],
        calibration_variables["firm_lb2"],
        calibration_variables["firm_ub1"],
        calibration_variables["firm_ub2"],
        calibration_variables["firm_alpha1"],
        calibration_variables["firm_alpha2"],
        calibration_variables["firm_rho"],
    )
    firm_equity = np.where(firm_equity > 10**8, 10**6, firm_equity)
    firm_supply = np.where(firm_supply > 10**10, 10**6, firm_supply)
    firm_profit = np.array([0 for x in range(calibration_variables["FIRMS"])])

    firm_price = calibration_variables["market_price"] + np.random.normal(
        0, 0.01 * calibration_variables["market_price"], calibration_variables["FIRMS"]
    )
    return (
        firm_equity,
        firm_prod,
        firm_ex_supply,
        firm_wage,
        firm_pd,
        firm_supply,
        firm_profit,
        firm_price,
        firm_max_leverage,
    )
