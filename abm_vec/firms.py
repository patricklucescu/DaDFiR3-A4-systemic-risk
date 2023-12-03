import numpy as np


def check_loan_desire_and_choose_loans(
    firm_credit_demand, num_firms, num_banks, max_bank_loan, bank_weights
):
    """
    | Function that assigns banks for firms that need a loan.

    :param firm_credit_demand: Vector of credit demand for each firm
    :param num_firms: Number of firms
    :param num_banks: Number of banks
    :param max_bank_loan: Max banks to which a firm can apply for loan
    :param bank_weights: Weights for the banks.
    :return: Array of num_firms x num_banks where an entry 1 in (i,j) specified that firm i wants loan from bank j
    """

    firm_loan_needed = firm_credit_demand > 0
    loan_indicator = np.zeros((num_firms, num_banks))
    # Indices of firms needing a loan
    firms_needing_loan = np.where(firm_loan_needed)[0]
    # Generate random permutations of bank indices for each firm needing a loan
    random_bank_permutations = np.apply_along_axis(
        lambda row: np.random.choice(
            row, size=num_banks, replace=False, p=list(bank_weights)
        ),
        1,
        np.tile(np.arange(num_banks), (firms_needing_loan.size, 1)),
    )
    # Take the first two banks from each permutation
    chosen_banks = random_bank_permutations[:, :max_bank_loan]
    # Create an array of indices to select the appropriate elements in loan_interest
    firm_indices = np.repeat(firms_needing_loan[:, np.newaxis], max_bank_loan, axis=1)
    # Set the loan interest for the chosen banks to 1
    loan_indicator[firm_indices, chosen_banks] = 1
    return loan_indicator


def get_loan_priority(row):
    non_zero_mask = row != 0
    sorted_non_zero_indices = np.argsort(row[non_zero_mask]) + 1
    final_indices = np.zeros_like(row, dtype=int)
    final_indices[non_zero_mask] = sorted_non_zero_indices
    return final_indices


def shuffle_firms(
    num_firms,
    firm_equity,
    firm_prod,
    firm_ex_supply,
    firm_wage,
    firm_pd,
    firm_supply,
    firm_profit,
    firm_price,
    firm_max_leverage,
):
    """
    | Shuffle the order of the firms.

    :param num_firms: Number of firms
    :param firm_equity: Vector of firm equity
    :param firm_prod: Vector of firm productivity
    :param firm_ex_supply: Vector of firm excess supply
    :param firm_wage: Vector of firm wage
    :param firm_pd: Vector of firm probability of default
    :param firm_supply: Vector of firm supply
    :param firm_profit: Vector of firm profit
    :param firm_price: Vector of firm price
    :param firm_max_leverage: Vector of firm maximum leverage
    :return: Tuple of shuffled firm variables
    """

    new_index = np.random.permutation(range(num_firms))
    return (
        firm_equity[new_index],
        firm_prod[new_index],
        firm_ex_supply[new_index],
        firm_wage[new_index],
        firm_pd[new_index],
        firm_supply[new_index],
        firm_profit[new_index],
        firm_price[new_index],
        firm_max_leverage[new_index],
    )


def get_non_zero_values_from_matrix(matrix):
    """
    | Returns a dictionary with row indices as keys and tuples of non-zero values and indices as values.

    Parameters:
    matrix (numpy array): A 2D numpy array.

    Returns:
    dict: A dictionary with row indices as keys and tuples of non-zero values and indices as values.
    """
    return {
        row_index: [
            (col_index, value)
            for col_index, value in zip(np.where(row != 0)[0], row[row != 0])
        ]
        for row_index, row in enumerate(matrix)
    }
