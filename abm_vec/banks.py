import numpy as np
from numpy import ndarray


def asses_loan_requests_firms(
    loan_indicator: ndarray,
    firm_credit_demand: ndarray,
    bank_max_credit: ndarray,
    firm_pd: ndarray,
    firm_financial_fragility: ndarray,
    policy_rate: float,
    theta: float,
) -> ndarray:
    """
    | Asses firms loan requests and compute interest rates.

    | The function operates by first determining which firms are eligible for loans based on their demand and the
    maximum credit available from banks. It then calculates the interest rate for each loan using a combination of the
    policy rate and two random factors that are influenced by the firm's probability of default and financial fragility.

    :param loan_indicator: matrix indicating if firm i is interested in bank j
    :param firm_credit_demand: credit demanded by firms
    :param bank_max_credit: maximum bank credit
    :param firm_pd: firm probability of default
    :param firm_financial_fragility: firm financial probability
    :param policy_rate: Regulator policy rate
    :param theta: parameter controlling randomness
    :return: Matrix with interest rates
    """

    # Conditions
    condition = (loan_indicator > 0) & (
        firm_credit_demand[:, np.newaxis] < bank_max_credit
    )
    # Initialize interest array
    loan_interest = np.zeros_like(loan_indicator, dtype=float)
    # Find indices where condition is True
    indices = np.where(condition)
    # Calculate the number of true elements in condition
    num_true_elements = condition.sum()

    # Generate random_factor1 for each true element
    random_factor1 = np.random.uniform(0, theta, size=num_true_elements)
    # Generate random_factor2 as before
    random_factor2 = np.tanh(
        (1 + np.random.uniform(0.9, 1.1, size=num_true_elements) * firm_pd[indices[0]])
        * firm_financial_fragility[indices[0]]
    )
    # Apply calculation only where condition is met
    loan_interest[indices] = policy_rate * (1 + random_factor1 * random_factor2)
    return loan_interest


def asses_interbank_loans(
    financial_fragility: ndarray,
    policy_rate: float,
    num_requests: float | int,
    theta: float,
) -> ndarray:
    """
    | Compute the interbank loan request for a bank. Similar to firms but a bit simpler.

    | It takes into account the financial fragility of the bank and the policy rate. It also uses a random factor.

    :param financial_fragility: Financial fragility of the bank that wants to borrow money
    :param policy_rate: Policy rate
    :param num_requests: Number of loan requests
    :param theta: Theta used for randomness
    :return: Interbank loan interest rate
    """

    random_factor1 = np.random.uniform(0, theta, size=num_requests)
    return policy_rate * (1 + random_factor1 * np.tanh(financial_fragility))


def provide_cds_spread(
    prob_default: float, policy_rate: float, interest_rate: float
) -> float:
    """
    | Calculates and provides the spread value for a credit default swap (CDS) based on the Hull CDS
    valuation model for a one-period model.

    :param prob_default: Probability default of underlying firm
    :param policy_rate: Policy rate
    :param interest_rate: Loan interest rate
    :return: CDS spread value
    """

    recover_rate = 0.3
    q = prob_default + max(np.random.normal(0, 0.01), 10 ** (-2) - prob_default)
    u = 1 / (1 + policy_rate)
    v = 1 / (1 + policy_rate)
    e = 1 / (1 + policy_rate)
    A = interest_rate
    pi = 1 - q
    return (1 - recover_rate - A * recover_rate) * q * v / (q * (u + e) + pi * u)


def check_cds(
    deposit: float,
    loan_liability: float,
    loan_asset: float,
    equity: float,
    cds_asset: float,
    premium: float,
) -> bool:
    """
    | Checks if the CDS can be granted based on the maximum credit limit and other loan and asset amounts.

    :param cds_asset: Current CDS asset value of the bank
    :param equity: Equity of the bank
    :param loan_asset: Current loan asset of the bank
    :param loan_liability: Current loan liability of the bank
    :param deposit: Deposit value of the bank
    :param premium: The CDS premium
    :return: True if CDS can be granted, False otherwise
    """
    return deposit + loan_liability + equity - loan_asset + cds_asset >= premium