import copy
import random

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy.optimize import minimize
from scipy.stats import kstest

from abm_vec.abm_simulation import run_simulation
from abm_vec.essentials import get_git_root_directory
from abm_vec.initialization import get_bank_data

bank_data = get_bank_data()


def min_fun(x):
    param = {
        "firm_lb1": x[0],
        "firm_lb2": x[1],
        "firm_ub1": x[2],
        "firm_ub2": x[3],
        "firm_alpha1": x[4],
        "firm_alpha2": x[5],
        "firm_rho": x[6],
        "min_productivity": x[7],
        "market_price": x[8],
    }
    emp, sim = run_simulation(1, copy.deepcopy(bank_data), param)
    return -kstest(emp, sim, alternative="two-sided").pvalue


bounds = [
    (5 * 10**5, 5 * 10**6),
    (10**3, 10**4),
    (5 * 10**7, 30 * 10**7),
    (5 * 10**5, 10**7),
    (0, 3),
    (0, 3),
    (0, 1),
    (100, 1000),
    (50, 2000),
]

initial_guess = [10**6, 7500, 15 * 10**7, 0.7 * 10**6, 1.6, 1.7, 0.9, 150, 820]


result = minimize(min_fun, initial_guess, method="Nelder-Mead", bounds=bounds)

optimal_x = result.x

param = {
    "firm_lb1": optimal_x[0],
    "firm_lb2": optimal_x[1],
    "firm_ub1": optimal_x[2],
    "firm_ub2": optimal_x[3],
    "firm_alpha1": optimal_x[4],
    "firm_alpha2": optimal_x[5],
    "firm_rho": optimal_x[6],
    "min_productivity": optimal_x[7],
    "market_price": optimal_x[8],
}

emp, sim = run_simulation(1, copy.deepcopy(bank_data), param)


#### PLOTTING ####
git_root = get_git_root_directory()
plot_dir = git_root + "/plots/"

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
sns.histplot(emp, legend="Empirical", color="blue", ax=axes[0])
sns.histplot(sim, legend="Simulation", color="orange", ax=axes[1])
axes[0].set_title("Empirical")
axes[1].set_title("Simulated")
fig.suptitle("Histogram of Loan-to-Equity Ratio", fontsize=16)
plt.tight_layout()
fig.subplots_adjust(top=0.88)
fig.savefig(plot_dir + "loan_to_equity_ratio.png", dpi=300)
plt.show()


## Q-Q plot
quantiles1 = np.percentile(sim, np.linspace(0, 100, 100))
quantiles2 = np.percentile(emp, np.linspace(0, 100, 100))

fig = plt.figure(figsize=(6, 6))
plt.scatter(quantiles1, quantiles2)
plt.xlabel("Simulated")
plt.ylabel("Empirical")
plt.title("Q-Q Plot")
plt.plot(
    [quantiles1.min(), quantiles1.max()],
    [quantiles1.min(), quantiles1.max()],
    ls="--",
    c=".3",
)
fig.savefig(plot_dir + "qq_loan_to_equity_ratio.png", dpi=300)
plt.show()


### Mini simulation ###
from joblib import Parallel, delayed


def fun(seed=1, bank_data=None):
    param = {
        "firm_lb1": optimal_x[0],
        "firm_lb2": optimal_x[1],
        "firm_ub1": optimal_x[2],
        "firm_ub2": optimal_x[3],
        "firm_alpha1": optimal_x[4],
        "firm_alpha2": optimal_x[5],
        "firm_rho": optimal_x[6],
        "min_productivity": optimal_x[7],
        "market_price": optimal_x[8],
    }
    e, s = run_simulation(seed, copy.deepcopy(bank_data), param)
    return kstest(e, s, alternative="two-sided").pvalue


random_seeds = random.sample(range(1, 100000), 1000)

results = Parallel(n_jobs=-1)(delayed(fun)(i, bank_data) for i in random_seeds)

fig = plt.figure(figsize=(6, 6))
plt.hist(results, bins=50)
plt.show()

# array([9.85306867e+05, 7.80304587e+03, 1.51534168e+08, 7.02465046e+05,
#        1.66464979e+00, 1.66480151e+00, 9.36365504e-01, 1.40908624e+02,
#        8.16166428e+02])
