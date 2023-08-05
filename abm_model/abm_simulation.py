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
from abm_model.calibration import *
import itertools
import numpy as np
import matplotlib.pyplot as plt
from abm_model.SRISK_calculation import calculate_SRISK

#get calibration variables for initialization and markov model
calibration_variables = get_calibration_variables()

#assign variables
FIRMS = calibration_variables['FIRMS']
BANKS = calibration_variables['BANKS']
T = calibration_variables['T']
covered_cds_prob = calibration_variables['covered_cds_prob']
naked_cds_prob = calibration_variables['naked_cds_prob']




# generate unique indices for the firms and banks
firms_idx = [f'firm_{x}' for x in range(1, FIRMS + 1)]
banks_idx = [f'bank_{x}' for x in range(1, BANKS + 1)]
firms, banks, base_agent, base_firm, base_bank = generate_random_firms_and_banks(firms_idx, banks_idx, calibration_variables)

# Initialize Markov Model
starting_prob = calibration_variables['starting_prob']
states = calibration_variables['states']
transition_matrix = calibration_variables['transition_matrix']
economy_state = MarkovModel(starting_prob=starting_prob,
                            transition_matrix=transition_matrix,
                            states=states)

# good consumption based on economy state
good_consumption = calibration_variables['good_consumption']
good_consumption_std = calibration_variables['good_consumption_std']
min_consumption = calibration_variables['min_consumption']
max_consumption = calibration_variables['max_consumption']

# create logs and initialize historic values
logs = []
historic_data = {}
market_data = {}
statement_counter = {1: 0, 2: 0, 3: 0, 4: 0}
loan_desire = []
total_wages = []

#  TODO: add logs of defaulted firm object and bank object

# begin the simulation part
for t in range(T):
    start = time.time()

    start_of_period_firm_equity = sum([firms[firm_id].equity for firm_id in firms])
    # for each firm compute expected supply and see who wants loans
    ###print(f"Period {t}: Compute expected supply and price")
    for firm_id in firms.keys():
        firms[firm_id].prev_equity = firms[firm_id].equity
        firms[firm_id].compute_expected_supply_and_prices()
        firms[firm_id].check_loan_desire_and_choose_loans()

        if (firms[firm_id].excess_supply > 0 and firms[firm_id].price >= base_firm.market_price):
            statement_counter[1] += 1
        if (firms[firm_id].excess_supply == 0 and firms[firm_id].price < base_firm.market_price):
            statement_counter[2] += 1
        if (firms[firm_id].excess_supply > 0 and firms[firm_id].price < base_firm.market_price):
            statement_counter[3] += 1
        if (firms[firm_id].excess_supply == 0 and firms[firm_id].price >= base_firm.market_price):
            statement_counter[4] += 1

    loan_desire_firms = firms

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
    ###print(f"Period {t}: Create network connections")
    firms, banks, interbank_contracts, logs, period_t_transactions = create_network_connections(loan_offers,
                                                                         banks,
                                                                         firms,
                                                                         logs,
                                                                         base_agent.bank_ids,
                                                                         covered_cds_prob,
                                                                         naked_cds_prob,
                                                                         t)

    loan_granted_firms = firms

    # compute market price
    base_firm.change_market_price(np.median([firm.price for _, firm in firms.items()]))

    # Figure out firm default and update CDS recovery rate accordingly
    ###print(f"Period {t}: Get defaulting firms")
    firms, banks, defaulted_firms = clear_firm_default(firms,
                                                       banks,
                                                       economy_state,
                                                       good_consumption,
                                                       good_consumption_std,
                                                       min_consumption,
                                                       max_consumption,
                                                       calibration_variables['firm_equity_scaling'])

    # do deposit change
    for bank_id in base_agent.bank_ids:
        rv = np.random.normal(calibration_variables['mu_deposit_growth'], calibration_variables['std_deposit_growth']) / 100
        banks[bank_id].deposit_change = rv * banks[bank_id].deposits
        banks[bank_id].deposits += banks[bank_id].deposit_change
        # TODO: adjust the deposit variable

    # now figure out the banks network payments
    ###print(f"Period {t}: Get defaulting banks")
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
                              period_t_transactions,
                              loan_desire_firms,
                              loan_granted_firms)

    # reset banks and firms and remove defaulting ones
    banks = {bank_id: bank_entity for bank_id, bank_entity in banks.items() if bank_id not in defaulted_banks}
    defaulted_firms_entities = {firm_id: firm_entity for firm_id, firm_entity in firms.items() if firm_id in defaulted_firms}
    firms = {firm_id: firm_entity for firm_id, firm_entity in firms.items() if firm_id not in defaulted_firms}

    for bank_id in banks:
        banks[bank_id].reset_variables()
    for firm_id in firms:
        firms[firm_id].reset_variables()

    # create new bank entities and update the bank and firm ids list in the base agent
    max_id_firm = max([int(firm_id[5:]) for firm_id in base_agent.firm_ids])
    max_id_bank = max([int(bank_id[5:]) for bank_id in base_agent.bank_ids])
    new_firm_ids = [f'firm_{x}' for x in range(max_id_firm + 1, max_id_firm + 1 + len(defaulted_firms))]
    new_bank_ids = [f'bank_{x}' for x in range(max_id_bank + 1, max_id_bank + 1 + len(defaulted_banks))]
    new_max_leverage = [defaulted_firms_entities[firm_id].max_leverage for firm_id in defaulted_firms]
    firms, banks = generate_new_entities(new_bank_ids,
                                         new_firm_ids,
                                         banks,
                                         firms,
                                         defaulted_firms_entities,
                                         base_firm,
                                         calibration_variables,
                                         new_max_leverage)

    # regulate firm equity to be constant over time
    end_of_period_firm_equity = sum([firms[firm_id].equity for firm_id in firms])
    # dividend or share issues
    required_equity_correction = end_of_period_firm_equity / start_of_period_firm_equity
    #apply equity correction and calculate net-equity "profit"
    for firm_id in firms:
           firms[firm_id].equity = (1/required_equity_correction) * firms[firm_id].equity * (1 + np.random.normal(0,0.01))
           firms[firm_id].profit = float(firms[firm_id].equity / firms[firm_id].prev_equity - 1)

    # update base agent for new IDs
    updated_firm_ids = [firm_id for firm_id in (base_agent.firm_ids + new_firm_ids) if firm_id not in defaulted_firms]
    updated_bank_ids = [bank_id for bank_id in (base_agent.bank_ids + new_bank_ids) if bank_id not in defaulted_banks]
    base_agent.change_firm_ids(updated_firm_ids)
    base_agent.change_bank_ids(updated_bank_ids)

    # do calculations for next period
    economy_state.get_next_state()

    end = time.time()
    ###print(f"Period {t} finished in {(end-start)/60} minutes")


print(f'zero excess supply:{(statement_counter[2]+statement_counter[4])/(statement_counter[1]+statement_counter[2]+statement_counter[3]+statement_counter[4])}')

srisk = calculate_SRISK(historic_data['banks_equity_by_time'],historic_data['banks_equity_by_bank'],historic_data['banks_debt_by_bank'])












