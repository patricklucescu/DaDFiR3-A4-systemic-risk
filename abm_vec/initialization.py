import os
import random

import numpy as np
import pandas as pd
from scipy.stats import multivariate_normal, norm

from abm_vec.essentials import compute_pd, get_git_root_directory


def truncated_pareto_inv(y, alpha, lb, ub):
    return (
        -(y * ub**alpha - y * lb**alpha - ub**alpha) / (lb**alpha * ub**alpha)
    ) ** (-1 / alpha)


def boundedParetoNormal(size, lb1, lb2, ub1, ub2, alpha1, alpha2, rho):
    marginal_distribution = multivariate_normal(mean=[0, 0], cov=[[1, rho], [rho, 1]])
    random_samples_marginal = marginal_distribution.rvs(size=size)
    copula_samples = norm.cdf(random_samples_marginal)
    x1 = truncated_pareto_inv(copula_samples[:, 0], alpha1, lb1, ub1)
    x2 = truncated_pareto_inv(copula_samples[:, 1], alpha2, lb2, ub2)
    return x1, x2


def get_bank_data():
    """
    | Loads the bank data from the excel file and returns it as a dictionary.
    :return: dictionary with bank data
    """
    bank_df = pd.read_excel(
        os.path.join(get_git_root_directory(), "data/banks-swiss.xlsx")
    )
    bank_df = bank_df[
        (bank_df["Total Deposits"] != "-")
        & (bank_df["Gross Loans"] != "-")
        & (bank_df["Total Corp. Loans"] != "-")
    ]
    bank_df = bank_df.iloc[1:, :]
    bank_df.reset_index(inplace=True, drop=True)
    bank_df["bank_id"] = bank_df.index.map(lambda x: f"bank_{x + 1}")
    # get the bank data
    bank_equity = bank_df["Total Equity"].values * 10**6
    bank_deposits = bank_df["Total Deposits"].values * 10**6
    bank_loans = bank_df["Total Corp. Loans"].values * 10**6
    # t1 cap is a ratio and should not be multiplied by 10^6.
    bank_t1_cap = bank_df["Tier 1 Cap. Ratio"].values
    return {
        "equity": bank_equity,
        "deposits": bank_deposits,
        "loans": bank_loans,
        "t1_cap": bank_t1_cap,
    }


def generate_random_entities(calibration_variables: dict) -> tuple:
    """
    | Generates Firms and Banks based on the calibration settings. Firms are generated randomly while banks are
    initialized based on the swiss bank data.

    :param calibration_variables: Dictionary containing all calibration settings from calibration.py
    :return: A tuple containing the generated firms & banks vectors of info.
    """

    # get firm data
    # firm_equity = np.array(
    #     [
    #         max(
    #             calibration_variables["firm_equity_scaling"] * x,
    #             calibration_variables["firm_equity_scaling"] * 0.5,
    #         )
    #         for x in np.random.poisson(
    #             calibration_variables["firm_equity_poisson_lambda"],
    #             calibration_variables["FIRMS"],
    #         )
    #     ]
    # )
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
    # firm_supply = np.array(
    #     [
    #         max(
    #             calibration_variables["firm_supply_scaling"] * x,
    #             calibration_variables["firm_supply_scaling"] * 0.5,
    #         )
    #         for x in np.random.poisson(
    #             calibration_variables["firm_supply_poisson_lambda"],
    #             calibration_variables["FIRMS"],
    #         )
    #     ]
    # )
    firm_equity, firm_supply = boundedParetoNormal(
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
