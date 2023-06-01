from abm_model.initialization import generate_random_firms_and_banks
from abm_model.essentials import *
from abm_model.logs import LogMessage
import random
from numpy import random as npr
import itertools

# set up number of firms and banks and other parameters needed
FIRMS = 100
BANKS = 10
T = 10

# generate unique indices for the firms and banks
firms_idx = [f'firm_{x}' for x in range(1, FIRMS + 1)]
banks_idx = [f'bank_{x}' for x in range(1, BANKS + 1)]
firms, banks = generate_random_firms_and_banks(firms_idx, banks_idx)

# create logs
logs = []

# begin the simulation part
for t in range(T):
    # for each firm compute expected supply and see who wants loans
    for firm_id in firms.keys():
        firms[firm_id].compute_expected_supply_and_prices()
        firms[firm_id].check_loan_desire_and_choose_loans()

    # aggregate all loan request and see if bank agree
    loan_requests = merge_dict(list(itertools.chain(*[[{loan.lender: loan} for loan in firms[firm_id].potential_lenders]
                                                      for firm_id in firms.keys()])))

    # iterate through banks and see who accepts which ones accept the loans
    loan_offers = []
    for bank_id in banks.keys():
        banks[bank_id].update_max_credit()
        loan_offers += banks[bank_id].asses_loan_request_firms(loan_requests.get(bank_id, []))

    loan_offers = merge_dict([{loan.borrower: loan} for loan in loan_offers])
    loan_offers = {firm_id: sorted(loan_offers[firm_id], key=lambda y: y.interest_rate) for firm_id in loan_offers}
    # now generate random order for the firms to claim their loans
    loan_clearing_order = random.sample(list(firms.keys()), len(list(firms.keys())))
    # start the network allocation of loans and cds
    for firm_id in loan_clearing_order:
        loan_extended = False
        loans_offered = loan_offers[firm_id]
        for loan in loans_offered:
            break



