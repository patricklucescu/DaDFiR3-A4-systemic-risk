from abm_model.credit_default_swap import CDS
from abm_model.initialization import generate_random_firms_and_banks
from abm_model.essentials import *
from abm_model.logs import LogMessage
from abm_model.return_evaluation import *
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
good_consumption_std = [0.2, 0.3]
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
                if (covered_cds_prob > 0 or naked_cds_prob > 0):
                    # determine which banks want cds on this loan
                    interested_cds_buyers = [bank_id for bank_id in banks if
                                             (banks[bank_id].decide_cds(covered=(loan.lender == bank_id)))]
                    # for each interested buyer, get offers from various bank according to max_cds_requests,
                    # including only banks that are neither the lender bank itself nor any interested buyer (and
                    # neither the bank as its own counterparty)
                    cds_offers = [
                        {bank_id_buyer: CDS(bank_id_buyer, counterparty_id, loan.borrower, loan.prob_default_borrower,
                                            loan.notional_amount, banks[counterparty_id].provide_cds_spread(loan))}
                        for bank_id_buyer in interested_cds_buyers
                        for counterparty_id in random.choices([x for x in banks_idx if
                                                               (x != banks[bank_id_buyer].idx and x != loan.lender
                                                                and x not in interested_cds_buyers)],
                                                              k=banks[bank_id_buyer].max_cds_requests)]

                    cds_offers = merge_dict(cds_offers)
                    cds_offers = {bank_id: sorted(cds_offers[bank_id], key=lambda y: y.spread) for bank_id in
                                  cds_offers}
                    # only consider the best offer (smallest spread)
                    cds_offers = {bank_id: cds_offers[bank_id][0] for bank_id in cds_offers}
                    # see if cds is affordable for buyer, add to transaction-list if so
                    cds_transactions = {bank_id: cds_offers[bank_id] for bank_id in cds_offers
                                        if banks[bank_id].check_cds(cds_offers[bank_id].spread * loan.notional_amount)}
                    # enter transactions
                    for bank_id in cds_transactions:
                        banks[cds_transactions[bank_id].buyer].assets['cds'].append(cds_transactions[bank_id])
                        banks[cds_transactions[bank_id].seller].liabilities['cds'].append(cds_transactions[bank_id])
                        logs.append(LogMessage(
                            message=f'CDS sold from {cds_transactions[bank_id].seller} to '
                                    f'{cds_transactions[bank_id].buyer} on {cds_transactions[bank_id].reference_entity}'
                            ,
                            time=t,
                            data=cds_transactions[bank_id]
                        ))

    # adjust production based on Credit Market & do the good consumption market
    overall_consumption = good_consumption[economy_state.current_state]
    consumption_std = good_consumption_std[economy_state.current_state]
    for firm_id in firms.keys():
        firms[firm_id].adjust_production()
        firms[firm_id].produce_supply_consumption(min_consumption,
                                                  max_consumption,
                                                  overall_consumption,
                                                  consumption_std)

    # see which firms remain solvent
    defaulted_firms = [firms[firm_id].idx for firm_id in firms.keys() if firms[firm_id].check_default()]
    # do payments for firms
    for firm_id in firms.keys():
        # decide how much money you have
        loans = firms[firm_id].loans()
        total_loans = sum([(1 + loan.interest_rate) * loan.notional_amount for loan in loans])
        adjustment_factor = total_loans if firm_id not in defaulted_firms else firms[firm_id].equity
        for loan in firms[firm_id].loans():
            # payback
            #TODO: this is not correct
            banks[loan.lender].equity += ((1 + loan.interest_rate) * loan.notional_amount
                                          * adjustment_factor / total_loans)

        firms[firm_id].equity -= adjustment_factor


    # do calculations for next period
    # deposit shock
    economy_state.get_next_state()







    # end of period payoff-realization and bankruptcy evaluation

    #firm liqduity/bankruptcy
    #loan repayment incl. intersest rate
    #cds payment
    #bank defaults

    historic_bank_equity = update_history(historic_bank_equity, banks, t)
