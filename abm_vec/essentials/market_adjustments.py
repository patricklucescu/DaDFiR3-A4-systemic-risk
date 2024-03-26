import numpy as np

max_increase_wages = 0.02
max_increase_prices = 0.02
max_increase_quantity = 0.02


def price_adj_vectorized(n_sample: int) -> np.ndarray:
    """
    | Generate an array of random price adjustments.

    :param n_sample: Number of random adjustments to generate.
    :return: Random number.
    """
    return np.random.uniform(0, max_increase_prices, n_sample)


def supply_adj_vectorized(n_sample: int) -> np.ndarray:
    """
    | Generate an array of random supply adjustments.

    :param n_sample: Number of random adjustments to generate.
    :return: Random number.
    """
    return np.random.uniform(0, max_increase_quantity, n_sample)


def wages_adj_vectorized(n_sample: int) -> np.ndarray:
    """
    | Generate an array of random adjustments.

    :param n_sample: Number of random adjustments to generate.
    :return: Array of random numbers.
    """

    return np.random.uniform(-max_increase_wages, max_increase_wages, n_sample)


def wages_adj(w_vec: np.ndarray, min_wage: float) -> np.ndarray:
    """
    | Adjust a vector of wages with random adjustments.

    :param w_vec: Vector of wages.
    :param min_wage: Minimum wage.
    :return: Adjusted wages.
    """

    adjustment_factors = 1 + wages_adj_vectorized(len(w_vec))
    adjusted_wages = w_vec * adjustment_factors
    return np.maximum(min_wage, adjusted_wages)
