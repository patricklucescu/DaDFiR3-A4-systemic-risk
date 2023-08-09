from abm_model.firms import BaseFirm, Firm
from abm_model.banks import BaseBank, Bank
from abm_model.baseclass import BaseAgent
from abm_model.calibration import anaylse_calibration
import numpy as np
import random


def generate_random_firms_and_banks(firms_ids: list,
                                    banks_ids: list,
                                    calibration_variables: dict) -> tuple:
    """
    | Generates random firms and banks based on the given firm and bank IDs.

    :param firms_ids: A list of firm IDs.
    :param banks_ids: A list of bank IDs.
    :param calibration_variables: Dictonary containing all calibration settings from calibration.py
    :return: A tuple containing the generated firms, banks, base agent, base firm, and base bank.
    """

    # base agent, base bank and base firm
    base_agent = BaseAgent()
    base_firm = BaseFirm()
    base_bank = BaseBank()
    base_agent.change_policy_rate(calibration_variables['policy_rate'])
    base_agent.change_firm_ids(firms_ids)
    base_agent.change_bank_ids(banks_ids)
    base_agent.change_max_bank_loan(calibration_variables['max_bank_loan'])
    base_agent.change_max_interbank_loan(calibration_variables['max_interbank_loan'])
    base_agent.change_max_cds_requests(calibration_variables['max_cds_requests'])
    base_firm.change_min_wage(int(calibration_variables['min_wage']))
    base_firm.change_min_max_leverage(int(calibration_variables['min_max_leverage']))
    base_firm.change_max_max_leverage(calibration_variables['max_max_leverage'])
    base_bank.change_h_theta(calibration_variables['h_theta'])
    base_firm.change_market_price(float((1+base_agent.policy_rate)*(base_firm.min_wage / calibration_variables['min_productivity'])))

    # create actual firms
    firms = {}
    firm_equity = [max(calibration_variables['firm_equity_scaling'] * x, calibration_variables['firm_equity_scaling'] * 0.5) for x in np.random.poisson(calibration_variables['firm_equity_poisson_lambda'], len(firms_ids))]
    productivity = [calibration_variables['min_productivity']] * len(firms_ids)
    excess_supply = [x for x in np.random.binomial(1, calibration_variables['firm_init_excess_supply_prob'], len(firms_ids))]
    max_leverage = [random.randint(base_firm.min_max_leverage, base_firm.max_max_leverage) for i in
                    range(len(firms_ids))]
    wage = [base_firm.min_wage + abs(np.random.normal(base_firm.min_wage*0.05,(base_firm.min_wage*0.1)**0.5)) for x in range(len(firms_ids))]
    supply = [max(calibration_variables['firm_supply_scaling'] * x, calibration_variables['firm_supply_scaling'] * 0.5) for x in np.random.poisson(calibration_variables['firm_supply_poisson_lambda'], len(firms_ids))]
    for i in range(len(firms_ids)):
        firms[firms_ids[i]] = Firm(
            idx=firms_ids[i],
            supply=supply[i],
            excess_supply=excess_supply[i],
            price=base_firm.market_price + np.random.normal(base_firm.market_price*0.2, (base_firm.market_price*0.2)**0.1),
            wage=wage[i],
            equity=firm_equity[i],
            productivity=productivity[i],
            max_leverage_firm=max_leverage[i],
            leverage_severity=calibration_variables['leverage_severity']
        )

    # create actual banks
    banks = {}
    bank_equity = [float(max(calibration_variables['bank_equity_scaling'] * x, calibration_variables['bank_equity_scaling'] * 0.5)) for x in np.random.poisson(calibration_variables['bank_supply_poisson_lambda'], len(banks_ids))]
    bank_deposit = [bank_equity[i] * random.randint(calibration_variables['min_deposit_ratio'],
                                                    calibration_variables['max_deposit_ratio'])
                                                    for i in range(0,len(bank_equity))]


    for i in range(len(banks_ids)):
        banks[banks_ids[i]] = Bank(idx=banks_ids[i],
                                   equity=bank_equity[i],
                                   deposits=bank_deposit[i],
                                   capital_requirement=calibration_variables['capital_req'],
                                   covered_cds_prob=calibration_variables['covered_cds_prob'],
                                   naked_cds_prob=calibration_variables['naked_cds_prob'])

    probability_excess_supply_zero = anaylse_calibration(calibration_variables, firms, banks)

    base_firm.change_prob_excess_supply(probability_excess_supply_zero)

    return firms, banks, base_agent, base_firm, base_bank


def generate_new_entities(new_bank_ids: list,
                          new_firm_ids: list,
                          banks: dict,
                          firms: dict,
                          defaulted_firms_entities: dict,
                          base_firm: BaseFirm,
                          calibration_variables: dict,
                          new_max_leverage: list) -> tuple:
    """
    | Generates new banks and firms based on the given new bank and firm IDs.

    :param new_bank_ids: A list of new bank IDs.
    :param new_firm_ids: A list of new firm IDs.
    :param banks: A dictionary of existing banks.
    :param firms: A dictionary of existing firms.
    :param defaulted_firms_entities: A dictionary of defaulted firms
    :param base_firm: The base firm object.
    :param covered_cds_prob: The probability of a covered credit default swap (CDS) being used.
    :param naked_cds_prob: The probability of a naked CDS being used.
    :return: A tuple containing the updated firms and banks.
    """

    covered_cds_prob = calibration_variables['covered_cds_prob']
    naked_cds_prob = calibration_variables['naked_cds_prob']
    leverage_severity = calibration_variables['leverage_severity']


    # for banks generation
    capital_req = calibration_variables['capital_req']
    average_equity = np.mean([banks[bank_id].equity for bank_id in banks.keys()])
    std_equity = np.std([banks[bank_id].equity for bank_id in banks.keys()])
    average_deposit = np.mean([banks[bank_id].deposits for bank_id in banks.keys()])
    std_deposit = np.std([banks[bank_id].deposits for bank_id in banks.keys()])
    bank_equity = list(np.random.normal(average_equity, std_equity**0.1, len(new_bank_ids)))
    bank_deposit = list(np.random.normal(average_deposit, std_deposit**0.1, len(new_bank_ids)))
    for i, bank_id in enumerate(new_bank_ids):
        banks[bank_id] = Bank(idx=bank_id,
                              equity=bank_equity[i],
                              deposits=bank_deposit[i],
                              capital_requirement=capital_req,
                              covered_cds_prob=covered_cds_prob,
                              naked_cds_prob=naked_cds_prob)
    # for firm generation
    average_supply = np.mean([firms[firm_id].supply for firm_id in firms.keys()])
    std_supply = np.std([firms[firm_id].supply for firm_id in firms.keys()])
    average_ex_supply = np.mean([firms[firm_id].excess_supply for firm_id in firms.keys()])
    std_ex_supply = np.std([firms[firm_id].excess_supply for firm_id in firms.keys()])
    average_price = np.mean([firms[firm_id].price for firm_id in firms.keys()])
    std_price = np.std([firms[firm_id].price for firm_id in firms.keys()])
    average_wage = np.mean([firms[firm_id].wage for firm_id in firms.keys()])
    std_wage = np.std([firms[firm_id].wage for firm_id in firms.keys()])
    average_firm_equity = np.mean([firms[firm_id].equity for firm_id in firms.keys()])
    std_firm_equity = np.std([firms[firm_id].equity for firm_id in firms.keys()])
    average_productivity = np.mean([firms[firm_id].productivity for firm_id in firms.keys()])
    std_productivity = np.std([firms[firm_id].productivity for firm_id in firms.keys()])
    average_default_prob = np.mean([firms[firm_id].default_probability for firm_id in firms.keys()])
    std_default_prob = np.std([firms[firm_id].default_probability for firm_id in firms.keys()])
    supply = [max(x, calibration_variables['firm_supply_scaling']) for x in np.random.normal(average_supply, std_supply, len(new_firm_ids))]
    excess_supply = [max(x, 0) for x in np.random.normal(average_ex_supply, std_ex_supply, len(new_firm_ids))]
    price = [max(x, base_firm.market_price / 2) for x in np.random.normal(average_price, std_price, len(new_firm_ids))]
    wage = [max(x, base_firm.min_wage) for x in np.random.normal(average_wage, std_wage, len(new_firm_ids))]
    firm_equity = [max(x, calibration_variables['firm_equity_scaling'] * 0.5) for x in np.random.normal(average_firm_equity, std_firm_equity, len(new_firm_ids))]
    max_leverage = new_max_leverage

    productivity = [calibration_variables['min_productivity']] * len(new_firm_ids)
    for i, firm_id in enumerate(new_firm_ids):
        firms[firm_id] = Firm(
            idx=firm_id,
            supply=supply[i],
            excess_supply=excess_supply[i],
            price=price[i],
            wage=wage[i],
            equity=firm_equity[i],
            productivity=productivity[i],
            max_leverage_firm = max_leverage[i],
            leverage_severity=leverage_severity
        )
    return firms, banks
