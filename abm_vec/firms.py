import numpy as np
from numpy import ndarray


def check_loan_desire_and_choose_loans(
    firm_credit_demand: ndarray,
    num_firms: ndarray,
    num_banks: ndarray,
    max_bank_loan: ndarray,
    bank_weights: ndarray,
) -> ndarray:
    """
    | The function identifies firms that want to take a loan and randomly selects banks to which they apply for a loan.

    | The following steps are performed:

    #. Identifies firms that need a loan, determined by whether their credit demand is greater than zero.

    #. For each firm identified as needing a loan, the function generates a random permutation of bank indices,
        respecting the `bank_weights` which indicate the likelihood of choosing each bank.

    #. From these permutations, the function selects the first `max_bank_loan` banks for each firm, representing the
    banks to which the firm will apply.

    # **Constructing Loan Indicator Matrix**:
        *  The function then constructs a loan indicator matrix of size num_firms x num_banks.
        *  The entry (i,j) in the matrix is 1 if firm i wants a loan from bank j, and 0 otherwise.

    :param firm_credit_demand: Vector of credit demand for each firm
    :param num_firms: Number of firms
    :param num_banks: Number of banks
    :param max_bank_loan: Max banks to which a firm can apply for loan
    :param bank_weights: Weights for the banks.
    :return: Array of num_firms x num_banks where an entry of 1 in (i,j) specifies that firm i wants a loan from bank j
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
    # Take the first max_bank_loan banks from each permutation
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
    num_firms: int,
    firm_equity: ndarray,
    firm_prod: ndarray,
    firm_ex_supply: ndarray,
    firm_wage: ndarray,
    firm_pd: ndarray,
    firm_supply: ndarray,
    firm_profit: ndarray,
    firm_price: ndarray,
    firm_max_leverage: ndarray,
) -> tuple:
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


def get_non_zero_values_from_matrix(matrix: ndarray) -> dict:
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
