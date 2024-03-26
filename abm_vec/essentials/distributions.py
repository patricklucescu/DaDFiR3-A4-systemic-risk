from numpy import ndarray
from scipy.stats import multivariate_normal, norm


def truncated_pareto_inv(y: ndarray, alpha: float, lb: float, ub: float) -> ndarray:
    """
    | Inverse of the truncated pareto distribution.
    | See https://en.wikipedia.org/wiki/Pareto_distribution#Truncated_Pareto_distribution
    for more information.

    :param y: Vector of values between 0 and 1.
    :param alpha: Pareto parameter
    :param lb: Lower bound
    :param ub: Upper bound
    :return: Vector of values between lb and ub.
    """
    return (
        -(y * ub**alpha - y * lb**alpha - ub**alpha) / (lb**alpha * ub**alpha)
    ) ** (-1 / alpha)


def bounded_pareto_normal(
    nsamples: int,
    lb1: float,
    lb2: float,
    ub1: float,
    ub2: float,
    alpha1: float,
    alpha2: float,
    rho: float,
) -> tuple[ndarray, ndarray]:
    """
    | Generate random samples from a bivariate normal distribution with bounded pareto marginals.

    :param nsamples: Number of samples to generate.
    :param lb1: Lower bound for first marginal.
    :param lb2: Lower bound for second marginal.
    :param ub1: Upper bound for first marginal.
    :param ub2: Upper bound for second marginal.
    :param alpha1: Pareto parameter for first marginal.
    :param alpha2: Pareto parameter for second marginal.
    :param rho: Correlation between the two marginals.
    :return: Tuple of two vectors of size nsamples.
    """
    marginal_distribution = multivariate_normal(mean=[0, 0], cov=[[1, rho], [rho, 1]])
    random_samples_marginal = marginal_distribution.rvs(size=nsamples)
    copula_samples = norm.cdf(random_samples_marginal)
    x1 = truncated_pareto_inv(copula_samples[:, 0], alpha1, lb1, ub1)
    x2 = truncated_pareto_inv(copula_samples[:, 1], alpha2, lb2, ub2)
    return x1, x2
