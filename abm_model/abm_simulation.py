from abm_model.initialization import generate_random_firms_and_banks
from abm_model.essentials import *
from abm_model.logs import LogMessage
from abm_model.credit_default_swap import CDS
from abm_model.markov_model import MarkovModel
import random
from numpy import random as npr
import itertools
import copy

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
good_consumption_std = [0.3, 0.2]
min_consumption = 0.1
max_consumption = 0.96

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
        loan_offers += banks[bank_id].asses_loan_requests(loan_requests.get(bank_id, []))

    loan_offers = merge_dict([{loan.borrower: loan} for loan in loan_offers])
    loan_offers = {firm_id: sorted(loan_offers[firm_id], key=lambda y: y.interest_rate) for firm_id in loan_offers}
    # now generate random order for the firms to claim their loans
    loan_clearing_order = random.sample(list(loan_offers.keys()), len(list(loan_offers.keys())))
    # start the network allocation of loans and cds
    for firm_id in loan_clearing_order:
        loans_offered = loan_offers[firm_id]
        loan_extended = False
        for loan in loans_offered:
            bank_condition = banks[loan.lender].check_loan(loan)
            if not bank_condition:
                continue
            elif bank_condition > 0:  # bank has enough money to extend the loan directly
                loan_extended = True
            else:
                credit_needed = - bank_condition
                interbank_loans = banks[loan.lender].get_potential_interbank_loans(credit_needed, loan.notional_amount)
                interbank_loans = [banks[bank_loan.lender].asses_loan_requests([bank_loan])
                                   for bank_loan in interbank_loans]
                interbank_loans = list(itertools.chain(*interbank_loans))
                interbank_loans = [bank_loan for bank_loan in interbank_loans
                                   if banks[bank_loan.lender].check_loan(bank_loan) > 0]
                interbank_loans = sorted(interbank_loans, key=lambda y: y.interest_rate)
                if len(interbank_loans) == 0:
                    continue
                bank_loan = interbank_loans[0]
                # extend the interbank loan
                banks[bank_loan.lender].assets['loans'].append(bank_loan)
                banks[bank_loan.borrower].liabilities['loans'].append(bank_loan)
                logs.append(LogMessage(
                    message=f'Interbank loan extended from {bank_loan.lender} to {bank_loan.borrower}',
                    time=t,
                    data=copy.deepcopy(bank_loan)
                ))
                # extend the firm loan
                loan_extended = True
            if loan_extended:
                banks[loan.lender].assets['loans'].append(loan)
                firms[loan.borrower].loans.append(loan)
                firms[loan.borrower].equity += loan.notional_amount
                logs.append(LogMessage(
                    message=f'Loan extended from {loan.lender} to {loan.borrower}',
                    time=t,
                    data=copy.deepcopy(loan)
                ))
                # Now start CDS market on this particular loan
                covered_cds_needed = banks[loan.lender].decide_cds(covered=True)
                cds_market_participants = [bank_id for bank_id in [x for x in banks.keys() if x != loan.lender] if
                                           banks[bank_id].decide_cds() == 1]
                random.shuffle(cds_market_participants)
                if covered_cds_needed and len(cds_market_participants) > 1:
                    # we need a covered cds so first participant is grouped with the covered cds seller
                    buyer = loan.lender
                    seller = cds_market_participants[0]
                    covered_cds = CDS(
                        buyer=buyer,
                        seller=seller,
                        reference_entity=loan.borrower,
                        default_probability=firms[loan.borrower].default_probability,
                        notional_amount=loan.notional_amount,
                        tenor=1,
                        risk_free_rate=base_agent.policy_rate
                    )
                    # TODO: compute the spread
                    covered_cds.update_spread(0.02)
                    banks[buyer].liabilities['cds'].append(covered_cds)
                    banks[seller].assets['cds'].append(covered_cds)
                    logs.append(LogMessage(
                        message=f'Covered CDS extended from {seller} to {buyer}',
                        time=t,
                        data=copy.deepcopy(covered_cds)
                    ))
                    cds_market_participants = cds_market_participants[1:]
                # naked cds only now
                # as list is already randomized just pick two consecutive elements to form a cds contract
                while len(cds_market_participants) > 1:
                    buyer = cds_market_participants[0]
                    seller = cds_market_participants[1]
                    naked_cds = CDS(
                        buyer=buyer,
                        seller=seller,
                        reference_entity=loan.borrower,
                        default_probability=firms[loan.borrower].default_probability,
                        notional_amount=loan.notional_amount,
                        tenor=1,
                        risk_free_rate=base_agent.policy_rate
                    )
                    # TODO: compute the spread
                    naked_cds.update_spread(0.02)
                    banks[buyer].liabilities['cds'].append(naked_cds)
                    banks[seller].assets['cds'].append(naked_cds)
                    logs.append(LogMessage(
                        message=f'Naked CDS extended from {seller} to {buyer}',
                        time=t,
                        data=copy.deepcopy(naked_cds)
                    ))
                    cds_market_participants = cds_market_participants[2:]

    # adjust production based on Credit Market & do the good consumption market
    overall_consumption = good_consumption[economy_state.current_state]
    consumption_std = good_consumption_std[economy_state.current_state]
    for firm_id in firms.keys():
        firms[firm_id].adjust_production()
        firms[firm_id].produce_supply_consumption(min_consumption,
                                                  max_consumption,
                                                  overall_consumption,
                                                  consumption_std)

    for firm_id in firms.keys():

        break











