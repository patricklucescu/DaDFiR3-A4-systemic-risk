from abm_model.firms import BaseFirm, Firm
from abm_model.banks import BaseBank, Bank
from abm_model.baseclass import BaseAgent
import numpy as np

h_theta = 0.1


def generate_random_firms_and_banks(firms_ids, banks_ids, covered_cds_prob, naked_cds_prob):
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
    base_firm.change_market_price(10)
    base_firm.change_min_wage(200)
    base_bank.change_h_theta(0.1)

    # create actual firms
    firms = {}
    firm_equity = [max(1000 * x,100) for x in np.random.poisson(4, len(firms_ids))]
    productivity = [0.3] * len(firms_ids)
    excess_supply = [100 * x for x in np.random.poisson(4, len(firms_ids))]
    supply = [max(400 * x, 70) for x in np.random.poisson(4, len(firms_ids))]
    price = [base_firm.market_price + np.random.normal(0, 0.3) for x in range(len(firms_ids))]
    wage = [base_firm.min_wage + np.random.exponential(4) for x in range(len(firms_ids))]
    default_probability = [max(x, 0.01) for x in np.random.beta(a=1.9, b=8, size=len(firms_ids))]
    for i in range(len(firms_ids)):
        firms[firms_ids[i]] = Firm(
            idx=firms_ids[i],
            supply=supply[i],
            excess_supply=excess_supply[i],
            price=price[i],
            wage=wage[i],
            equity=firm_equity[i],
            productivity=productivity[i],
            default_probability=default_probability[i]
        )

    # create actual banks
    banks = {}
    capital_req = 0.9
    bank_equity = [max(10000000/2, 10000000 * x) for x in np.random.poisson(4, len(banks_ids))]
    bank_deposit = [x/y for x, y in zip(bank_equity, np.random.beta(a=3, b=18, size=len(banks_ids)))]
    for i in range(len(banks_ids)):
        banks[banks_ids[i]] = Bank(idx=banks_ids[i],
                                   equity=bank_equity[i],
                                   deposits=bank_deposit[i],
                                   capital_requirement=capital_req,
                                   covered_cds_prob=covered_cds_prob,
                                   naked_cds_prob=naked_cds_prob)
    return firms, banks, base_agent, base_firm, base_bank
