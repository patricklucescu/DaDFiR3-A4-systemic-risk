import numpy as np
from scipy.stats import powerlaw
from scipy.stats import multivariate_normal


def fictitious_default(x, L):
    """
    Function implementing the Eisenberg and Noe clearning algorithm.
    
    x: outcome of the equity portfolios on the entities
    L: matrix of liabilities, with L_ij representing the liability of node i towards node j.
    :return: payments: payment vector 
    """
    Lbar = np.sum(L, axis=1)
    Pi = np.matmul(np.diag(1/Lbar) , L)
    Pi[Lbar == 0,:] = 0
    default = True
    default_set = 0.0
    payments = Lbar.copy()
    while default:
        wealth = x + np.matmul(Pi.T,payments)
        old_payments = payments.copy()
        default_set = [i for i in range(len(wealth)) if (wealth[i] - Lbar[i])<0] 
        payments[default_set] = wealth[default_set]
        if sum(1 for i in range(len(payments)) if np.abs(payments[i] - old_payments[i]) < 10 ** -6) == len(Lbar):
            default = False
    return payments


def generate_bank_portfolios(loc, scale, beta, market_tail_exp, sims):
    """
    Generate the bank's equity portoflios according to:
        r_i = n_i - b_i * e_m
    with n_i normal and e_m normalized power law
    """
    if not len(loc) == len(scale) == len(beta):
        raise ValueError("Loc, Scale and Beta need to have same length")
    n = multivariate_normal.rvs(loc, np.diag(scale), sims)
    p = powerlaw.rvs(market_tail_exp, size=sims)
    market_influence = np.array([b * p for b in beta]).T
    return n - market_influence