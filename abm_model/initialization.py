from abm_model.firms import BaseFirm, Firm
from abm_model.banks import BaseBank, Bank
from abm_model.baseclass import BaseAgent
import numpy as np

h_theta = 0.1


def generate_random_firms_and_banks(firms_ids: list,
                                    banks_ids: list,
                                    covered_cds_prob: float,
                                    naked_cds_prob: float) -> tuple:
    """
    | Generates random firms and banks based on the given firm and bank IDs.

    :param firms_ids: A list of firm IDs.
    :param banks_ids: A list of bank IDs.
    :param covered_cds_prob: The probability of a covered credit default swap (CDS) being used.
    :param naked_cds_prob: The probability of a naked CDS being used.
    :return: A tuple containing the generated firms, banks, base agent, base firm, and base bank.
    """
    min_productivity = 0.3

    # base agent, base bank and base firm
    base_agent = BaseAgent()
    base_firm = BaseFirm()
    base_bank = BaseBank()
    base_agent.change_policy_rate(0.02)
    base_agent.change_firm_ids(firms_ids)
    base_agent.change_bank_ids(banks_ids)
    base_agent.change_max_bank_loan(3)
    base_agent.change_max_interbank_loan(2)
    base_agent.change_max_cds_requests(3)
    base_firm.change_min_wage(200)
    base_firm.change_max_leverage(10)
    base_bank.change_h_theta(0.1)
    base_firm.change_market_price(float((1+base_agent.policy_rate)*(base_firm.min_wage / min_productivity)))

    # create actual firms
    firms = {}
    #adjustment factor 500 for 20 banks and 300 firms.
    adj_fact = 500
    firm_equity = [max(1000*adj_fact * x, 500*adj_fact) for x in np.random.poisson(4, len(firms_ids))]
    productivity = [min_productivity] * len(firms_ids)
    excess_supply = [100*10 * x for x in np.random.poisson(4, len(firms_ids))]
    # adjustment factor 500 for 20 banks and 300 firms.
    supply = [max(400*2 * x, 70*2) for x in np.random.poisson(4, len(firms_ids))]
    #price = [max(base_firm.market_price + np.random.normal(10, 5), 1.1*base_firm.market_price)
    #         for x in range(len(firms_ids))]
    wage = [base_firm.min_wage + np.random.exponential(4) for x in range(len(firms_ids))]
    default_probability = [max(x, 0.01) for x in np.random.beta(a=1.9, b=8, size=len(firms_ids))]
    for i in range(len(firms_ids)):
        firms[firms_ids[i]] = Firm(
            idx=firms_ids[i],
            supply=supply[i],
            excess_supply=excess_supply[i],
            price=max(base_firm.market_price + np.random.normal(10, 5), wage[i]/productivity[i]),
            wage=wage[i],
            equity=firm_equity[i],
            productivity=productivity[i],
            default_probability=default_probability[i]
        )

    # create actual banks
    banks = {}
    capital_req = 0.9
    bank_equity = [max(1000000 / 2, 1000000 * x) for x in np.random.poisson(4, len(banks_ids))]
    bank_deposit = [x / y for x, y in zip(bank_equity, np.random.beta(a=3, b=18, size=len(banks_ids)))]
    for i in range(len(banks_ids)):
        banks[banks_ids[i]] = Bank(idx=banks_ids[i],
                                   equity=bank_equity[i],
                                   deposits=bank_deposit[i],
                                   capital_requirement=capital_req,
                                   covered_cds_prob=covered_cds_prob,
                                   naked_cds_prob=naked_cds_prob)
    return firms, banks, base_agent, base_firm, base_bank


def generate_new_entities(new_bank_ids: list,
                          new_firm_ids: list,
                          banks: dict,
                          firms: dict,
                          base_firm: BaseAgent,
                          covered_cds_prob: float,
                          naked_cds_prob: float) -> tuple:
    """
    | Generates new banks and firms based on the given new bank and firm IDs.

    :param new_bank_ids: A list of new bank IDs.
    :param new_firm_ids: A list of new firm IDs.
    :param banks: A dictionary of existing banks.
    :param firms: A dictionary of existing firms.
    :param base_firm: The base firm object.
    :param covered_cds_prob: The probability of a covered credit default swap (CDS) being used.
    :param naked_cds_prob: The probability of a naked CDS being used.
    :return: A tuple containing the updated firms and banks.
    """
    # for banks generation
    capital_req = 0.9
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
    supply = [max(x, 70) for x in np.random.normal(average_supply, std_supply, len(new_firm_ids))]
    excess_supply = [max(x, 0) for x in np.random.normal(average_ex_supply, std_ex_supply, len(new_firm_ids))]
    price = [max(x, base_firm.market_price / 2) for x in np.random.normal(average_price, std_price, len(new_firm_ids))]
    wage = [max(x, base_firm.min_wage) for x in np.random.normal(average_wage, std_wage, len(new_firm_ids))]
    firm_equity = [max(x, 100) for x in np.random.normal(average_firm_equity, std_firm_equity, len(new_firm_ids))]
    default_probability = [max(x, 0.01) for x in np.random.normal(average_default_prob, std_default_prob,
                                                                  len(new_firm_ids))]
    productivity = [0.3] * len(new_firm_ids)
    for i, firm_id in enumerate(new_firm_ids):
        firms[firm_id] = Firm(
            idx=firm_id,
            supply=supply[i],
            excess_supply=excess_supply[i],
            price=price[i],
            wage=wage[i],
            equity=firm_equity[i],
            productivity=productivity[i],
            default_probability=default_probability[i]
        )
    return firms, banks
