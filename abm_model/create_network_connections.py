from abm_model.credit_default_swap import CDS
from abm_model.logs import LogMessage
import random
import copy
import itertools
from abm_model.essentials import *


def create_network_connections(loan_offers: dict,
                               banks: dict,
                               firms: dict,
                               logs: list,
                               banks_idx: list,
                               covered_cds_prob: float,
                               naked_cds_prob: float,
                               t: float) -> tuple:
    """
    | Create the Bank-to-Firm Loans, Bank-to-Bank Loans and the Bank-to-Bank CDS contracts.

    :param loan_offers: Dictionary that has as keys the firm ids and as values the possible loans.
    :param banks: Dictionary of banks.
    :param firms: Dictionary of Firms.
    :param logs: Log file containing all actions in the simulation.
    :param banks_idx: List of bank ids.
    :param covered_cds_prob: Probability a bank wants to buy a covered CDS.
    :param naked_cds_prob: Probability a bank wants to buy a naked CDS.
    :param t: Simulation current time.
    :return: List of variables of interest.
    """

    period_t_transactions = []

    # define list of all interbank contracts made in this period
    interbank_contracts = []
    # create a random order in which firms choose their loans
    loan_clearing_order = random.sample(list(loan_offers.keys()), len(list(loan_offers.keys())))
    # start the network allocation of loans and cds
    for firm_id in loan_clearing_order:
        loans_offered = loan_offers[firm_id]
        loan_extended = False
        for loan in loans_offered:
            bank_condition = banks[loan.lender].check_loan(loan)
            if not bank_condition:  # bank is above the maximum leverage if it accepts the loan
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
                interbank_contracts.append(copy.deepcopy(bank_loan))
                # extend the interbank loan
                banks[bank_loan.lender].current_deposits -= bank_loan.notional_amount
                banks[bank_loan.lender].assets['loans'].append(bank_loan)
                banks[bank_loan.borrower].liabilities['loans'].append(bank_loan)
                logs.append(LogMessage(
                    message=f'Interbank loan extended from {bank_loan.lender} to {bank_loan.borrower}',
                    time=t,
                    data=copy.deepcopy(bank_loan)
                ))
                period_t_transactions.append(LogMessage(
                    message=f'Interbank loan extended from {bank_loan.lender} to {bank_loan.borrower}',
                    time=t,
                    data=copy.deepcopy(bank_loan)
                ))
                # extend the firm loan
                loan_extended = True
            if loan_extended:
                banks[loan.lender].assets['loans'].append(loan)
                banks[loan.lender].current_deposits -= loan.notional_amount
                firms[loan.borrower].loans.append(loan)
                firms[loan.borrower].equity += loan.notional_amount
                logs.append(LogMessage(
                    message=f'Loan extended from {loan.lender} to {loan.borrower}',
                    time=t,
                    data=copy.deepcopy(loan)
                ))
                period_t_transactions.append(LogMessage(
                    message=f'Loan extended from {loan.lender} to {loan.borrower}',
                    time=t,
                    data=copy.deepcopy(loan)
                ))
                # Now start CDS market on this particular loan
                if covered_cds_prob > 0 or naked_cds_prob > 0:
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
                        interbank_contracts.append(cds_transactions[bank_id])
                        logs.append(LogMessage(
                            message=f'CDS sold from {cds_transactions[bank_id].seller} to '
                                    f'{cds_transactions[bank_id].buyer} on {cds_transactions[bank_id].reference_entity}'
                            ,
                            time=t,
                            data=copy.deepcopy(cds_transactions[bank_id])
                        ))
                        period_t_transactions.append(LogMessage(
                            message=f'CDS sold from {cds_transactions[bank_id].seller} to '
                                    f'{cds_transactions[bank_id].buyer} on {cds_transactions[bank_id].reference_entity}'
                            ,
                            time=t,
                            data=copy.deepcopy(cds_transactions[bank_id])
                        ))
                break

    return firms, banks, interbank_contracts, logs, period_t_transactions
