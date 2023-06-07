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
        loan_offers += banks[bank_id].asses_loan_requests(loan_requests.get(bank_id, []))

    loan_offers = merge_dict([{loan.borrower: loan} for loan in loan_offers])
    loan_offers = {firm_id: sorted(loan_offers[firm_id], key=lambda y: y.interest_rate) for firm_id in loan_offers}
    # now generate random order for the firms to claim their loans
    loan_clearing_order = random.sample(list(firms.keys()), len(list(firms.keys())))
    # start the network allocation of loans and cds
    # TODO: firm might have no loan, check beforehand to avoid key error
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
                # TODO: bank might be selected as own counterparty and loan was granted in one example (how?)
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
                    data=bank_loan.copy()
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
                    data=loan.copy()
                ))
                # Now start CDS market on this particular loan

                break






