from abm_model.firm import Firm
from abm_model.bank import Bank
import numpy as np

h_theta = 0.5

def generate_random_firms_and_banks(firms_idx, banks_idx):
    firms = {}

    market_price = 10
    min_wage = 200
    max_banks_loan=3
    base_equity = [1000 * x for x in np.random.poisson(4, len(firms_idx))]
    base_equity = [max(x, 100) for x in base_equity]
    productivity = [0.3] * len(firms_idx)
    supply = [100 * x for x in np.random.poisson(4, len(firms_idx))]
    price = [market_price + np.random.normal(0,0.3) for x in range(len(firms_idx))]
    wage=[min_wage+np.random.exponential(4) for x in range(len(firms_idx))]
    market_price = np.mean(price)

    for i in range(len(firms_idx)):
        firms[firms_idx[i]] = Firm(idx=firms_idx[i],
                                   market_price=market_price,
                                   supply=supply[i],
                                   price=price[i],
                                   min_wage = min_wage,
                                   wage=wage[i],
                                   equity_level = base_equity[i],
                                   productivity = productivity[i],
                                   firm_ids=firms_idx,
                                   bank_ids=banks_idx,
                                   loans=None,
                                   num_firms=len(firms_idx),
                                   num_banks=len(banks_idx),
                                   max_banks_loan=max_banks_loan)
    banks = {}
    capital_req = 0.9
    policy_rate = 0.02
    bank_equity = [10000000 * x for x in np.random.poisson(4, len(banks_idx))]
    bank_equity = [min(10000000/2, x) for x in bank_equity]
    for i in range(len(banks_idx)):
        banks[banks_idx[i]] = Bank(idx=banks_idx[i],
                                   firm_ids=firms_idx,
                                   bank_ids=banks_idx,
                                   equity=bank_equity[i],
                                   capital_req=capital_req,
                                   policy_rate=policy_rate,
                                   bank_loans=[],
                                   firm_loans=[],
                                   h_theta=h_theta)
    return firms, banks