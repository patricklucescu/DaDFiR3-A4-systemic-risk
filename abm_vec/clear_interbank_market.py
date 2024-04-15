import numpy as np
from numpy import ndarray


def clear_interbank_market(
    num_banks: int,
    loan_banks_interest: ndarray,
    loan_banks_amount: ndarray,
    recovery_rate: ndarray,
    defaulting_firms: ndarray,
    loan_firm_value: ndarray,
    bank_equity: ndarray,
    deposit_change: ndarray,
    bank_deposits: ndarray,
    bank_current_deposit: ndarray,
    cds_spread_amount: ndarray,
    cds_dict: dict,
):
    """
    | Processes the clearing of the interbank market, considering loans, defaults, and Credit Default Swaps (CDS),
    and updates the financial status of banks accordingly.

    | This function computes and adjusts the equity and deposits of banks based on interbank loans, CDS contracts,
     and defaults in the system. It takes into account the complex interactions between these elements to reflect the
     changes in the banks' financial state after market clearing.

    :param num_banks: Number of banks
    :param loan_banks_interest: Matrix of loans interest from each bank to each other bank
    :param loan_banks_amount: Matrix of loans amounts from each bank to each other bank
    :param recovery_rate: Vector of recovery rates of each firm
    :param defaulting_firms: Vector of defaulting firms
    :param loan_firm_value: Vector of loans value from each firm to each bank
    :param bank_equity: Vector of equity of each bank
    :param deposit_change: Change in deposits of each bank
    :param bank_deposits: Deposits of each bank
    :param bank_current_deposit: Current deposits of each bank
    :param cds_spread_amount: CDS spread payments of each bank
    :param cds_dict: Dictionary of cds contracts by firm
    :return:
    """

    # create liability matrix: assume row ows to column
    liabilities = np.zeros(shape=(num_banks, num_banks))
    # add interbank loans
    liabilities += (1 + loan_banks_interest) * loan_banks_amount
    # add cds spread payments
    liabilities += cds_spread_amount
    # add cds payments in case of default
    for firm_id in defaulting_firms:
        if firm_id in cds_dict:
            cds_liability = np.zeros((num_banks, num_banks))
            cds_liability[cds_dict[firm_id][2], cds_dict[firm_id][1]] = (
                1 - recovery_rate[firm_id]
            ) * cds_dict[firm_id][0]
            liabilities += cds_liability

    # see which bank are defaulting
    Lbar = np.sum(liabilities, axis=1)
    Lbar_inverse = np.zeros_like(Lbar, dtype=float)
    non_zero_mask = (Lbar != 0)
    Lbar_inverse[non_zero_mask] = 1 / Lbar[non_zero_mask]
    Pi = np.matmul(np.diag(Lbar_inverse), liabilities)
    default = True
    default_set = []
    payments = Lbar.copy()
    money_from_loan = np.sum(loan_firm_value, axis=0)
    initial_wealth = bank_equity + money_from_loan + np.minimum(deposit_change, 0)
    while default:
        wealth = initial_wealth + np.matmul(Pi.T, payments)
        old_payments = payments.copy()
        default_set = [i for i in range(len(wealth)) if (wealth[i] - Lbar[i]) < 0]
        payments[default_set] = wealth[default_set]
        if sum(
            1
            for i in range(len(payments))
            if np.abs(payments[i] - old_payments[i]) < 10**-6
        ) == len(Lbar):
            default = False

    bank_earnings = (
        bank_equity
        + money_from_loan
        + np.minimum(deposit_change, 0)
        + np.matmul(Pi.T, payments)
        - payments
    )

    money_for_deposits = (
        bank_deposits - bank_current_deposit - np.maximum(deposit_change, 0)
    )
    default_set = np.concatenate(
        (default_set, np.where(bank_earnings < money_for_deposits)[0])
    )
    default_set = default_set.astype(int)
    default_set = np.unique(default_set)
    # deal with defaulting banks
    if len(default_set) > 0:
        bank_equity[default_set] = 0
        bank_current_deposit[default_set] += bank_earnings[default_set]
        bank_deposits[default_set] = bank_current_deposit[default_set] + np.maximum(
            deposit_change[default_set], 0
            )
    # deal with non defaulting banks
    non_default = ~np.isin(np.arange(num_banks), default_set)
    bank_current_deposit[non_default] += money_for_deposits[non_default]
    bank_deposits[non_default] = bank_current_deposit[non_default] + np.maximum(
        deposit_change[non_default], 0
    )
    bank_equity[non_default] = (
        bank_earnings[non_default] - money_for_deposits[non_default]
    )

    return (
        default_set,
        bank_equity,
        bank_deposits,
        liabilities
    )
