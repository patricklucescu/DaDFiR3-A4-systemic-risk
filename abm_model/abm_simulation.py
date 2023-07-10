import copy
import time
from abm_model.initialization import generate_random_firms_and_banks, generate_new_entities
from abm_model.essentials import merge_dict
from abm_model.analytics import *
from abm_model.markov_model import MarkovModel
from abm_model.clear_interbank_market import clear_interbank_market
from abm_model.clear_firm_default import clear_firm_default
from abm_model.create_network_connections import create_network_connections
from abm_model.logs import LogMessage
import itertools
import numpy as np

# set up number of firms and banks and other parameters needed
FIRMS = 300
BANKS = 20
T = 400
covered_cds_prob = 0.5
naked_cds_prob = 0.1


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
good_consumption = [0.95, 0.90]
good_consumption_std = [0.1, 0.15]
min_consumption = 0.85
max_consumption = 1
#payout_ratio = [0.75, 0.25]

# create logs and initialize historic values
logs = []
historic_data = {}

#  TODO: add logs of defaulted firm oject and bank object

# begin the simulation part
for t in range(T):
    start = time.time()
    # for each firm compute expected supply and see who wants loans
    print(f"Period {t}: Compute expected supply and price")
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
    print(f"Period {t}: Create network connections")
    firms, banks, interbank_contracts, logs, period_t_transactions = create_network_connections(loan_offers,
                                                                         banks,
                                                                         firms,
                                                                         logs,
                                                                         base_agent.bank_ids,
                                                                         covered_cds_prob,
                                                                         naked_cds_prob,
                                                                         t)

    # compute market price
    base_firm.change_market_price(sum([firm.price * firm.supply for _, firm in firms.items()]) / sum([firm.supply for _, firm in firms.items()]))


    # Figure out firm default and update CDS recovery rate accordingly
    print(f"Period {t}: Get defaulting firms")
    firms, banks, defaulted_firms = clear_firm_default(firms,
                                                       banks,
                                                       economy_state,
                                                       good_consumption,
                                                       good_consumption_std,
                                                       min_consumption,
                                                       max_consumption)

    # do deposit change
    for bank_id in base_agent.bank_ids:
        rv = np.random.normal(0, 2) / 100
        banks[bank_id].deposit_change = rv * banks[bank_id].deposits
        banks[bank_id].deposits += banks[bank_id].deposit_change
        # TODO: adjust the deposit variable

    # now figure out the banks network payments
    print(f"Period {t}: Get defaulting banks")
    banks, defaulted_banks = clear_interbank_market(banks,
                                                    firms,
                                                    base_agent.bank_ids,
                                                    interbank_contracts,
                                                    defaulted_firms)

    # add logs for default
    for firm_id in defaulted_firms:
        logs.append(LogMessage(
            message=f'Firm {firm_id} has defaulted.',
            time=t,
            data=copy.deepcopy(firms[firm_id])
        ))
    for bank_id in defaulted_banks:
        logs.append(LogMessage(
            message=f'Bank {bank_id} has defaulted.',
            time=t,
            data=copy.deepcopy(banks[bank_id])
        ))

    # get historic values and print control variables for analytics
    historic_data = analytics(historic_data,
                              banks,
                              t,
                              T,
                              economy_state,
                              defaulted_banks,
                              base_firm,
                              base_agent,
                              defaulted_firms,
                              firms,
                              period_t_transactions)

    # reset banks and firms and remove defaulting ones
    banks = {bank_id: bank_entity for bank_id, bank_entity in banks.items() if bank_id not in defaulted_banks}
    firms = {firm_id: firm_entity for firm_id, firm_entity in firms.items() if firm_id not in defaulted_firms}
    for bank_id in banks:
        banks[bank_id].reset_variables()
    for firm_id in firms:
        firms[firm_id].reset_variables()
        if t > 0:
            dividend = max((firms[firm_id].equity / firms[firm_id].prev_equity) - 1,0)
            #firms[firm_id].equity -= payout_ratio[economy_state.current_state]*dividend*firms[firm_id].equity
            firms[firm_id].equity -= 0.15*dividend * firms[firm_id].equity

    # create new bank entities and update the bank and firm ids list in the base agent
    max_id_firm = max([int(firm_id[5:]) for firm_id in base_agent.firm_ids])
    max_id_bank = max([int(bank_id[5:]) for bank_id in base_agent.bank_ids])
    new_firm_ids = [f'firm_{x}' for x in range(max_id_firm + 1, max_id_firm + 1 + len(defaulted_firms))]
    new_bank_ids = [f'bank_{x}' for x in range(max_id_bank + 1, max_id_bank + 1 + len(defaulted_banks))]
    firms, banks = generate_new_entities(new_bank_ids,
                                         new_firm_ids,
                                         banks,
                                         firms,
                                         base_firm,
                                         covered_cds_prob,
                                         naked_cds_prob)

    # update base agent for new IDs
    updated_firm_ids = [firm_id for firm_id in (base_agent.firm_ids + new_firm_ids) if firm_id not in defaulted_firms]
    updated_bank_ids = [bank_id for bank_id in (base_agent.bank_ids + new_bank_ids) if bank_id not in defaulted_banks]
    base_agent.change_firm_ids(updated_firm_ids)
    base_agent.change_bank_ids(updated_bank_ids)

    # do calculations for next period
    economy_state.get_next_state()


    end = time.time()
    print(f"Period {t} finished in {(end-start)/60} minutes")
