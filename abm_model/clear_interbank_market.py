from abm_model.loan import Loan
from abm_model.credit_default_swap import CDS
import numpy as np


def clear_interbank_market(banks, banks_idx, interbank_contracts, defaulted_firms):
    """Do the market clearing for the banks network"""

    banks_idx.sort(key=lambda idx: int(idx[5:]))
    num_banks = len(banks_idx)
    # create liability matrix
    liabilities = np.zeros(shape=(num_banks, num_banks))
    for contract in interbank_contracts:
        if type(contract) == Loan:
            buyer = banks_idx.index(contract.borrower)
            seller = banks_idx.index(contract.seller)
            liabilities[buyer, seller] += contract.notional_amount * (1 + contract.interest_rate)
        else:
            buyer = banks_idx.index(contract.buyer)
            seller = banks_idx.index(contract.seller)
            if contract.reference_entity in defaulted_firms:
                liabilities[seller, buyer] += contract.notional_amount * (1 - contract.recovery_rate - contract.spread)
            else:
                liabilities[buyer, seller] += contract.spread * contract.notional_amount

    Lbar = np.sum(liabilities, axis=1)
    Pi = np.matmul(np.diag(1 / Lbar), liabilities)
    Pi[Lbar == 0, :] = 0
    default = True
    default_set = 0.0
    payments = Lbar.copy()
    initial_wealth = np.array([banks[idx].equity + banks[idx].money_from_firm_loans +
                               banks[idx].deposit_chage for idx in banks_idx])
    while default:
        wealth = initial_wealth + np.matmul(Pi.T, payments)
        old_payments = payments.copy()
        default_set = [i for i in range(len(wealth)) if (wealth[i] - Lbar[i]) < 0]
        payments[default_set] = wealth[default_set]
        if sum(1 for i in range(len(payments)) if np.abs(payments[i] - old_payments[i]) < 10 ** -6) == len(Lbar):
            default = False
    # now do the payments
    for bank_id, index in zip(banks_idx, range(len(banks_idx))):
        banks[bank_id].equity += (banks[bank_id].money_from_firm_loans + banks[bank_id].deposit_chage +
                                  np.matmul(Pi.T, payments)[index] - payments[index])

    # see what each banks owns to its depositors

    return banks
