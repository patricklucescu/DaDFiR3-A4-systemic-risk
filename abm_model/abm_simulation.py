from abm_model.initialization import generate_random_firms_and_banks
from abm_model.essentials import merge_dict
from abm_model.return_evaluation import *
from abm_model.markov_model import MarkovModel
from abm_model.clear_interbank_market import clear_interbank_market
from abm_model.clear_firm_default import clear_firm_default
from abm_model.create_network_connections import create_network_connections
import itertools
import numpy as np

# set up number of firms and banks and other parameters needed
FIRMS = 100
BANKS = 10
T = 10
covered_cds_prob = 0.8
naked_cds_prob = 0.2

# generate unique indices for the firms and banks
firms_idx = [f'firm_{x}' for x in range(1, FIRMS + 1)]
banks_idx = [f'bank_{x}' for x in range(1, BANKS + 1)]
firms, banks, base_agent, base_firm, base_bank = generate_random_firms_and_banks(firms_idx, banks_idx,
                                                                                 covered_cds_prob, naked_cds_prob)

# Initialize Markov Model
starting_prob = [1, 0]
states = {0: 'good', 1: 'bad'}
transition_matrix = np.array([[0.7, 0.3], [0.8, 0.2]])
economy_state = MarkovModel(starting_prob=starting_prob,
                            transition_matrix=transition_matrix,
                            states=states)

# good consumption based on economy state
good_consumption = [0.8, 0.6]
good_consumption_std = [0.2, 0.3]
min_consumption = 0.1
max_consumption = 1

# create logs
logs = []
historic_bank_equity = {}

# begin the simulation part
for t in range(T):
    # for each firm compute expected supply and see who wants loans
    for firm_id in firms.keys():
        firms[firm_id].compute_expected_supply_and_prices()
        firms[firm_id].check_loan_desire_and_choose_loans()

    # iterate through banks and see which ones accept the loans
    loan_requests = merge_dict(list(itertools.chain(*[[{loan.lender: loan} for loan in firms[firm_id].potential_lenders]
                                                      for firm_id in firms.keys()])))
    loan_offers = []
    for bank_id in banks.keys():
        banks[bank_id].update_current_deposits()
        banks[bank_id].update_max_credit()
        loan_offers += banks[bank_id].asses_loan_requests(loan_requests.get(bank_id, []))
    loan_offers = merge_dict([{loan.borrower: loan} for loan in loan_offers])
    loan_offers = {firm_id: sorted(loan_offers[firm_id], key=lambda y: y.interest_rate) for firm_id in loan_offers}

    # start the network allocation of loans and cds
    firms, banks, interbank_contracts, logs = create_network_connections(loan_offers,
                                                                         banks,
                                                                         firms,
                                                                         logs,
                                                                         banks_idx,
                                                                         covered_cds_prob,
                                                                         naked_cds_prob,
                                                                         t)

    # Figure out firm default and update CDS recovery rate accordingly
    firms, banks, defaulted_firms = clear_firm_default(firms,
                                                       banks,
                                                       economy_state,
                                                       good_consumption,
                                                       good_consumption_std,
                                                       min_consumption,
                                                       max_consumption)

    # do deposit change
    for bank_id in banks_idx:
        rv = np.random.normal(0,1)/100
        banks[bank_id].deposit_change = rv * banks[bank_id].deposits
        banks[bank_id].deposits += banks[bank_id].deposit_change
        # TODO: adjust the deposit variable

    # now figure out the banks network payments
    banks = clear_interbank_market(banks, base_agent.bank_ids, interbank_contracts, defaulted_firms)

    # get defaulting banks

    # do calculations for next period
    # deposit shock
    economy_state.get_next_state()

    # end of period payoff-realization and bankruptcy evaluation

    # firm liqduity/bankruptcy
    # loan repayment incl. intersest rate
    # cds payment
    # bank defaults

    historic_bank_equity = update_history(historic_bank_equity, banks, t)
