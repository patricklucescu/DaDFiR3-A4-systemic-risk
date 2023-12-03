import os
import random

import numpy as np
import pandas as pd

from abm_model.banks import Bank, BaseBank
from abm_model.baseclass import BaseAgent
from abm_model.essentials import compute_pd, get_git_root_directory
from abm_model.firms import BaseFirm, Firm


def generate_random_entities(firms_ids: list, calibration_variables: dict) -> tuple:
    """
    | Generates Firms and Banks based on the calibration settings. Firms are generated randomly while banks are
    initialized based on the european bank data.

    :param firms_ids: A list of firm IDs.
    :param calibration_variables: Dictionary containing all calibration settings from calibration.py
    :return: A tuple containing the generated firms, banks, base agent, base firm, and base bank.
    """

    # load bank data
    bank_df = pd.read_excel(
        os.path.join(get_git_root_directory(), "data/banks-swiss.xlsx")
    )
    bank_df = bank_df[
        (bank_df["Total Deposits"] != "-")
        & (bank_df["Gross Loans"] != "-")
        & (bank_df["Total Corp. Loans"] != "-")
    ]  # &
    # (bank_df['Tier 1 Cap. Ratio'] != '-')]
    bank_df = bank_df.iloc[1:, :]
    bank_df.reset_index(inplace=True, drop=True)
    bank_df["bank_id"] = bank_df.index.map(lambda x: f"bank_{x + 1}")
    bank_data = dict()
    for _, row in bank_df.iterrows():
        bank_data[row["bank_id"]] = {
            "equity": row["Total Equity"],
            "deposits": row["Total Deposits"],
            "loans": row["Total Corp. Loans"],
            "tier_1_cap": row["Tier 1 Cap. Ratio"],
            "name": row["Entity Name"],
        }
    banks_ids = list(bank_data.keys())

    base_agent = BaseAgent()
    base_firm = BaseFirm()
    base_bank = BaseBank()
    base_agent.change_policy_rate(calibration_variables["policy_rate"])
    base_agent.change_firm_ids(firms_ids)
    base_agent.change_bank_ids(banks_ids)
    base_agent.change_max_bank_loan(calibration_variables["max_bank_loan"])
    base_agent.change_max_interbank_loan(calibration_variables["max_interbank_loan"])
    base_agent.change_max_cds_requests(calibration_variables["max_cds_requests"])
    base_firm.change_min_wage(calibration_variables["min_wage"])
    base_firm.change_min_max_leverage(int(calibration_variables["min_max_leverage"]))
    base_firm.change_max_max_leverage(calibration_variables["max_max_leverage"])
    base_bank.change_h_theta(calibration_variables["h_theta"])
    base_firm.change_market_price(calibration_variables["market_price"])
    base_firm.change_prob_excess_supply(
        calibration_variables["firm_init_excess_supply_prob"]
    )

    # create random firms
    firms = {}
    firm_equity = [
        max(
            calibration_variables["firm_equity_scaling"] * x,
            calibration_variables["firm_equity_scaling"] * 0.5,
        )
        for x in np.random.poisson(
            calibration_variables["firm_equity_poisson_lambda"], len(firms_ids)
        )
    ]
    productivity = [calibration_variables["min_productivity"]] * len(firms_ids)
    excess_supply = [
        x
        for x in np.random.binomial(
            1, calibration_variables["firm_init_excess_supply_prob"], len(firms_ids)
        )
    ]
    wage = [
        base_firm.min_wage
        + abs(
            np.random.normal(
                base_firm.min_wage * 0.05, (base_firm.min_wage * 0.1) ** 0.5
            )
        )
        for x in range(len(firms_ids))
    ]
    max_leverage = [
        random.randint(base_firm.min_max_leverage, base_firm.max_max_leverage)
        for i in range(len(firms_ids))
    ]
    supply = [
        max(
            calibration_variables["firm_supply_scaling"] * x,
            calibration_variables["firm_supply_scaling"] * 0.5,
        )
        for x in np.random.poisson(
            calibration_variables["firm_supply_poisson_lambda"], len(firms_ids)
        )
    ]
    for i in range(len(firms_ids)):
        firms[firms_ids[i]] = Firm(
            idx=firms_ids[i],
            supply=supply[i],
            excess_supply=excess_supply[i],
            price=base_firm.market_price
            + np.random.normal(0, 0.01 * base_firm.market_price),
            wage=wage[i],
            equity=firm_equity[i],
            productivity=productivity[i],
            max_leverage_firm=max_leverage[i],
            leverage_severity=calibration_variables["leverage_severity"],
        )

    # create actual banks
    banks = {}
    for i in range(len(banks_ids)):
        banks[banks_ids[i]] = Bank(
            idx=banks_ids[i],
            equity=bank_data[banks_ids[i]]["equity"] * 10**6,
            deposits=bank_data[banks_ids[i]]["deposits"] * 10**6,
            capital_requirement=calibration_variables["capital_req"],
            covered_cds_prob=calibration_variables["covered_cds_prob"],
            naked_cds_prob=calibration_variables["naked_cds_prob"],
            tier_1_cap=bank_data[banks_ids[i]]["tier_1_cap"],
            gross_loans=bank_data[banks_ids[i]]["loans"] * 10**6,
        )

    return firms, banks, base_agent, base_firm, base_bank


def generate_new_entities(
    new_bank_ids: list,
    new_firm_ids: list,
    banks: dict,
    firms: dict,
    base_firm: BaseFirm,
    calibration_variables: dict,
    new_max_leverage: list,
) -> tuple:
    """
    | Generates new banks and firms based on the given new bank and firm IDs.

    :param new_bank_ids: A list of new bank IDs.
    :param new_firm_ids: A list of new firm IDs.
    :param banks: A dictionary of existing banks.
    :param firms: A dictionary of existing firms.
    :param base_firm: The base firm object.
    :param calibration_variables: The calibration variables
    :param new_max_leverage: the new max leverages as a list
    :return: A tuple containing the updated firms and banks.
    """

    covered_cds_prob = calibration_variables["covered_cds_prob"]
    naked_cds_prob = calibration_variables["naked_cds_prob"]
    leverage_severity = calibration_variables["leverage_severity"]
    equity_leverage = calibration_variables["equity_leverage"]

    # bank generation
    capital_req = calibration_variables["capital_req"]
    average_equity = np.mean([banks[bank_id].equity for bank_id in banks.keys()])
    std_equity = np.std([banks[bank_id].equity for bank_id in banks.keys()])
    average_deposit = np.mean([banks[bank_id].deposits for bank_id in banks.keys()])
    std_deposit = np.std([banks[bank_id].deposits for bank_id in banks.keys()])
    average_tier_1 = np.mean(
        [
            banks[bank_id].tier_1_cap
            for bank_id in banks.keys()
            if banks[bank_id].tier_1_cap != "-"
        ]
    )
    std_tier_1 = np.std(
        [
            banks[bank_id].tier_1_cap
            for bank_id in banks.keys()
            if banks[bank_id].tier_1_cap != "-"
        ]
    )
    average_gross_loans = np.mean(
        [banks[bank_id].gross_loans for bank_id in banks.keys()]
    )
    std_tier_gross_loans = np.std(
        [banks[bank_id].gross_loans for bank_id in banks.keys()]
    )
    bank_equity = list(
        np.random.normal(average_equity, std_equity**0.1, len(new_bank_ids))
    )
    bank_deposit = list(
        np.random.normal(average_deposit, std_deposit**0.1, len(new_bank_ids))
    )
    bank_tier_1 = list(
        np.random.normal(average_tier_1, std_tier_1**0.1, len(new_bank_ids))
    )
    bank_gross_loans = list(
        np.random.normal(
            average_gross_loans, std_tier_gross_loans**0.1, len(new_bank_ids)
        )
    )
    for i, bank_id in enumerate(new_bank_ids):
        banks[bank_id] = Bank(
            idx=bank_id,
            equity=bank_equity[i],
            deposits=bank_deposit[i],
            capital_requirement=capital_req,
            covered_cds_prob=covered_cds_prob,
            naked_cds_prob=naked_cds_prob,
            tier_1_cap=bank_tier_1[i],
            gross_loans=bank_gross_loans[i],
        )

    # firm generation
    average_supply = np.mean([firms[firm_id].supply for firm_id in firms.keys()])
    std_supply = np.std([firms[firm_id].supply for firm_id in firms.keys()])
    average_ex_supply = np.mean(
        [firms[firm_id].excess_supply for firm_id in firms.keys()]
    )
    std_ex_supply = np.std([firms[firm_id].excess_supply for firm_id in firms.keys()])
    average_price = np.mean([firms[firm_id].price for firm_id in firms.keys()])
    std_price = np.std([firms[firm_id].price for firm_id in firms.keys()])
    average_wage = np.mean([firms[firm_id].wage for firm_id in firms.keys()])
    std_wage = np.std([firms[firm_id].wage for firm_id in firms.keys()])
    average_firm_equity = np.mean([firms[firm_id].equity for firm_id in firms.keys()])
    std_firm_equity = np.std([firms[firm_id].equity for firm_id in firms.keys()])
    supply = [
        max(x, calibration_variables["firm_supply_scaling"])
        for x in np.random.normal(average_supply, std_supply, len(new_firm_ids))
    ]
    excess_supply = [
        max(x, 0)
        for x in np.random.normal(average_ex_supply, std_ex_supply, len(new_firm_ids))
    ]
    price = [
        max(x, base_firm.market_price / 2)
        for x in np.random.normal(average_price, std_price, len(new_firm_ids))
    ]
    wage = [
        max(x, base_firm.min_wage)
        for x in np.random.normal(average_wage, std_wage, len(new_firm_ids))
    ]
    firm_equity = [
        max(x, calibration_variables["firm_equity_scaling"] * 0.5)
        for x in np.random.normal(
            average_firm_equity, std_firm_equity, len(new_firm_ids)
        )
    ]
    max_leverage = new_max_leverage
    productivity = [calibration_variables["min_productivity"]] * len(new_firm_ids)
    for i, firm_id in enumerate(new_firm_ids):
        firms[firm_id] = Firm(
            idx=firm_id,
            supply=supply[i],
            excess_supply=excess_supply[i],
            price=price[i],
            wage=wage[i],
            equity=firm_equity[i],
            productivity=productivity[i],
            max_leverage_firm=max_leverage[i],
            leverage_severity=leverage_severity,
        )
        return firms, banks
