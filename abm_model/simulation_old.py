import numpy as np
from abm_model.initialization import generate_random_firms_and_banks
from abm_model.essentials import *
from abm_model.logs import LogMessage
import random
from numpy import random as npr
from operator import itemgetter

# set up number of firms and banks and other parameters needed
FIRMS = 10
BANKS = 2
T = 10
MAX_FIRMS_BUY = 3

# generate unique indices for the firms and banks
firms_idx = [f'firm_{x}' for x in range(1, FIRMS + 1)]
banks_idx = [f'bank_{x}' for x in range(1, BANKS + 1)]

firms, banks = generate_random_firms_and_banks(firms_idx, banks_idx)
min_wage = firms['firm_1'].min_wage

# create logs
logs = []
# begin the simulation part
for t in range(T):
    # TODO: first check who defaulted and start clearing mechanism

    # update firm and bank ids

    # assuming nobody defaulted

    # update the firm  and bank ids for Firm classes
    for x in firms.keys():
        firms[x].update_min_wage(min_wage)
        # update the firm  and bank ids for Firm classes
        firms[x].update_firm_ids(firms_idx)
        firms[x].update_firm_ids(banks_idx)
        # each firm computes desired credit required based on updated prices
        firms[x].compute_expected_supply_and_prices()
        firms[x].check_loan_desire_and_choose_loans()

    # aggregate all loan request and see if bank agree
    loan_requests = merge_dict([firms[x].potential_lenders for x in firms.keys()])
    # iterate through banks and see who accepts which ones accept the loans
    loan_offers = []
    for x in banks.keys():
        # first see how much credit each bank can give
        banks[x].update_max_credit()
        loan_offers += banks[x].asses_loan_requests(loan_requests[x], firms)

    # now see for each firm which loan they accept & sort the list of offers in ascending order of interest rate
    loan_offers = merge_dict(loan_offers)
    loan_offers = {x: sorted(loan_offers[x], key=lambda y: y[1]) for x in loan_offers}
    # now generate random order for the firms to claim their loans
    loan_clearing_order = random.sample(list(firms.keys()), len(list(firms.keys())))
    # start to loan program
    for firm_id in loan_clearing_order:
        loans_offered = loan_offers[firm_id]
        for loan in loans_offered:  # loan = (bank_id, interest_rate, credit_requested)
            bank_id = loan[0]
            interest_rate = loan[1]
            credit_requested = loan[2]
            if banks[bank_id].equity > credit_requested:  # just do the money transfer
                firms[firm_id].equity_level += credit_requested
                banks[bank_id].equity -= credit_requested
                firms[firm_id].loans += [(firm_id, bank_id, interest_rate, credit_requested)]
                banks[bank_id].firm_loans += [(firm_id, bank_id, interest_rate, credit_requested)]
                logs += [LogMessage(message=f"Loan from bank {bank_id} to firm {firm_id} has been extended",
                                    time=t,
                                    data=[(firm_id, bank_id, interest_rate, credit_requested)])]
                # if loan has been extended then no need to go over the rest of the loans
                break
            else:
                # TODO: implement this
                credit_demand = credit_requested - banks[bank_id].equity
                # bank does not have enough money to extend the loan
                # they attempt to borrow from another bank
                print(2)

        # now adjust production based on money for firms
        firms[firm_id].adjust_production()

    # produce supply
    goods_market_info = []
    for firm_id in firms.keys():
        goods_market_info.append(firms[firm_id].produce_supply())
    # create individuals to consume goods
    individuals = []
    for info in goods_market_info:
        individuals.extend([{'money': info[2]}] * info[1])

    # Start good markets consumption
    # decide how much each individual is going to consume
    consumption_levels = [u if u < 20 else 20 for u in npr.exponential(scale=4, size=len(individuals))]
    f = lambda x: -0.015 * x + 0.8
    consumption_levels = [f(c) for c in consumption_levels]
    individuals = [{'consumption': c, 'money': indiv['money']} for indiv, c in zip(individuals, consumption_levels)]

    for individual in random.sample(individuals, len(individuals)):
        max_money = individual['consumption'] * individual['money']
        random_firms = random.choices(list(firms.keys()), k=MAX_FIRMS_BUY)
        # sort firms based on price of product
        random_firms = sorted(random_firms, key=lambda y: firms[y].price)
        for firm_id in random_firms:
            max_supply_per_individual = max_money / firms[firm_id].price
            if firms[firm_id].created_supply > max_supply_per_individual:
                firms[firm_id].equity_level += max_money
                firms[firm_id].created_supply -= max_supply_per_individual
                break
            else:
                max_money_firm = firms[firm_id].price * firms[firm_id].created_supply
                max_money -= max_money_firm
                firms[firm_id].equity_level += max_money_firm
                firms[firm_id].created_supply = 0

    # CDS market
    # first compute firms default probabilities
    
