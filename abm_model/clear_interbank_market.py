from abm_model.loan import Loan
from abm_model.credit_default_swap import CDS
import numpy as np


def clear_interbank_market(banks, firms, banks_idx, interbank_contracts, defaulted_firms):
    """Do the market clearing for the banks network"""

    banks_idx.sort(key=lambda idx: int(idx[5:]))
    num_banks = len(banks_idx)
    # create liability matrix
    liabilities = np.zeros(shape=(num_banks, num_banks))
    for contract in interbank_contracts:
        if type(contract) == Loan:
            buyer = banks_idx.index(contract.borrower)
            seller = banks_idx.index(contract.lender)
            liabilities[buyer, seller] += contract.notional_amount * (1 + contract.interest_rate)
        else:
            buyer = banks_idx.index(contract.buyer)
            seller = banks_idx.index(contract.seller)
            #I think netting-out the spread is wrong. It is part of the liability matrix and adds to the total payment vector
            # ... Also, if recovery_rate is very close to 1, s.t. 1-R-spread < 0, you add negative entries to the liability matrix
            # ... which should not happen.
            if contract.reference_entity in defaulted_firms:
                liabilities[seller, buyer] += (contract.notional_amount *
                                               (1 - firms[contract.reference_entity].recovery_rate))
            liabilities[buyer, seller] += contract.spread * contract.notional_amount

    Lbar = np.sum(liabilities, axis=1)
    Pi = np.matmul(np.diag(1 / Lbar), liabilities)
    Pi[Lbar == 0, :] = 0
    default = True
    default_set = 0.0
    payments = Lbar.copy()
    # TODO: something is wrong here, how to adjust initial wealth: we only shift liabilities
    #  but i could save other banks by using deposits
    initial_wealth = np.array([banks[idx].equity + banks[idx].money_from_firm_loans +
                               min([banks[idx].deposit_change, 0]) for idx in banks_idx])
    while default:
        wealth = initial_wealth + np.matmul(Pi.T, payments)
        old_payments = payments.copy()
        default_set = [i for i in range(len(wealth)) if (wealth[i] - Lbar[i]) < 0]
        payments[default_set] = wealth[default_set]
        if sum(1 for i in range(len(payments)) if np.abs(payments[i] - old_payments[i]) < 10 ** -6) == len(Lbar):
            default = False
    # now do the payments
    for bank_id, index in zip(banks_idx, range(len(banks_idx))):
        banks[bank_id].earnings = (banks[bank_id].equity + banks[bank_id].money_from_firm_loans +
                                   min([banks[bank_id].deposit_change, 0]) + np.matmul(Pi.T, payments)[index]
                                   - payments[index])

    # check defaulting banks now
    defaulted_banks = [banks_idx[idx] for idx in default_set]
    for bank_id in banks_idx:
        money_for_deposits = banks[bank_id].deposits - banks[bank_id].current_deposits
        if bank_id in defaulted_banks or banks[bank_id].earnings < money_for_deposits:
            #  bank is in default
            defaulted_banks.append(bank_id)
            banks[bank_id].equity = 0
            banks[bank_id].current_deposits += banks[bank_id].earnings
            banks[bank_id].deposits = banks[bank_id].current_deposits
        else:
            #  bank is not in default
            banks[bank_id].current_deposits += money_for_deposits
            banks[bank_id].deposits = banks[bank_id].current_deposits
            banks[bank_id].equity = banks[bank_id].earnings - money_for_deposits
    defaulted_banks = list(np.array(defaulted_banks))
    return banks, defaulted_banks
