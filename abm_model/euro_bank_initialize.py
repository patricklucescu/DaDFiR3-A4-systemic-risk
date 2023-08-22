import pandas as pd
import os
from abm_model.firms import BaseFirm, Firm
from abm_model.banks import BaseBank, Bank
from abm_model.baseclass import BaseAgent
from abm_model.essentials import get_git_root_directory, compute_pd
import numpy as np
import random


def generate_random_entities(firms_ids: list,
                             calibration_variables: dict) -> tuple:
    """
    | Generates Firms and Banks based on the calibration settings. Firms are generated randomly while banks are
    initialized based on the european bank data.

    :param firms_ids: A list of firm IDs.
    :param calibration_variables: Dictionary containing all calibration settings from calibration.py
    :return: A tuple containing the generated firms, banks, base agent, base firm, and base bank.
    """


    # load bank data
    bank_df = pd.read_excel(os.path.join(get_git_root_directory(), 'abm_model/data/bankseuro_portfolios.xlsx'))
    bank_df = bank_df[(bank_df['Total Deposits'] != '-') &
                      (bank_df['Gross Loans'] != '-') &
                      (bank_df['Total Equity'] != '-') &
                      (bank_df['Tier 1 Cap. Ratio'] != '-')]
    bank_df.reset_index(inplace=True, drop=True)
    bank_df['bank_id'] = bank_df.index.map(lambda x: f'bank_{x+1}')
    bank_data = dict()
    for _, row in bank_df.iterrows():
        bank_data[row['bank_id']] = {
            'equity': row['Total Equity'],
            'deposits': row['Total Deposits'],
            'loans': row['Gross Loans'],
            'tier_1_cap': row['Tier 1 Cap. Ratio'],
            'name': row['Entity Name']
        }
    banks_ids = list(bank_data.keys())

    base_agent = BaseAgent()
    base_firm = BaseFirm()
    base_bank = BaseBank()
    base_agent.change_policy_rate(calibration_variables['policy_rate'])
    base_agent.change_firm_ids(firms_ids)
    base_agent.change_bank_ids(banks_ids)
    base_agent.change_max_bank_loan(calibration_variables['max_bank_loan'])
    base_agent.change_max_interbank_loan(calibration_variables['max_interbank_loan'])
    base_agent.change_max_cds_requests(calibration_variables['max_cds_requests'])
    base_firm.change_min_wage(calibration_variables['min_wage'])
    base_firm.change_max_leverage(calibration_variables['min_max_leverage'])
    base_bank.change_h_theta(calibration_variables['h_theta'])
    base_firm.change_market_price(
        float((1 + base_agent.policy_rate) * (base_firm.min_wage / calibration_variables['min_productivity'])))

    # create random firms
    firms = {}
    firm_equity = [
        max(calibration_variables['firm_equity_scaling'] * x, calibration_variables['firm_equity_scaling'] * 0.5) for x
        in np.random.poisson(calibration_variables['firm_equity_poisson_lambda'], len(firms_ids))]
    productivity = [calibration_variables['min_productivity']] * len(firms_ids)
    excess_supply = [x for x in
                     np.random.binomial(1, calibration_variables['firm_init_excess_supply_prob'], len(firms_ids))]
    wage = [base_firm.min_wage + abs(np.random.normal(base_firm.min_wage * 0.05, (base_firm.min_wage * 0.1) ** 0.5)) for
            x in range(len(firms_ids))]

    supply = [max(calibration_variables['firm_supply_scaling'] * x, calibration_variables['firm_supply_scaling'] * 0.5)
              for x in np.random.poisson(calibration_variables['firm_supply_poisson_lambda'], len(firms_ids))]
    default_probability = compute_pd(len(firms_ids))
    for i in range(len(firms_ids)):
        firms[firms_ids[i]] = Firm(
            idx=firms_ids[i],
            supply=supply[i],
            excess_supply=excess_supply[i],
            price=base_firm.market_price + np.random.normal(base_firm.market_price * 0.2,
                                                            (base_firm.market_price * 0.2) ** 0.1),
            wage=wage[i],
            equity=firm_equity[i],
            productivity=productivity[i],
            default_probability=default_probability[i]
        )

    # create actual banks
    banks = {}
    for i in range(len(banks_ids)):
        banks[banks_ids[i]] = Bank(idx=banks_ids[i],
                                   equity=bank_data[banks_ids[i]]['equity'],
                                   deposits=bank_data[banks_ids[i]]['deposits'],
                                   capital_requirement=calibration_variables['capital_req'],
                                   covered_cds_prob=calibration_variables['covered_cds_prob'],
                                   naked_cds_prob=calibration_variables['naked_cds_prob'],
                                   tier_1_cap=bank_data[banks_ids[i]]['tier_1_cap'],
                                   gross_loans=bank_data[banks_ids[i]]['loans'])

    return firms, banks, base_agent, base_firm, base_bank