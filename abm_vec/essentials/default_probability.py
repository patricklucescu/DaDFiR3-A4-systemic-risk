import numpy as np

RATINGS_DIST = {
    "AAA": [0.001, 0.03],
    "AA": [0.01, 0.1],
    "A": [0.02, 0.2],
    "BBB": [0.1, 0.5],
    "BB": [0.5, 2.5],
    "B": [2, 10],
}


def compute_pd(num_firms):
    """
    | Computes the probabilities of default based on credit rating distribution.

    :param num_firms: number of firms
    :return: the probabilities of default
    """
    ratings = ["AAA", "AA", "A", "BBB", "BB", "B"]
    probabilities = [0.01, 0.04, 0.15, 0.35, 0.25, 0.2]
    ratings = np.random.choice(ratings, p=probabilities, size=num_firms)
    prob_default = [
        np.random.uniform(RATINGS_DIST[rating][0], RATINGS_DIST[rating][1]) / 100
        for rating in ratings
    ]
    return prob_default
