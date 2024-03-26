from abm_vec.one_period_sim import run_one_sim
from abm_vec.initialization import get_bank_data
from abm_vec.calibration import get_calibration_variables
from joblib import Parallel, delayed
import pickle
import random
import copy
import numpy as np


def main():
    bank_data = get_bank_data()
    calibration_variables = get_calibration_variables()
    cds_covered = [0.  , 0.05, 0.1 , 0.15, 0.2 , 0.25, 0.3 , 0.35, 0.4 , 0.45, 0.5 ]
    cds_naked = [0.   , 0.005, 0.01 , 0.015, 0.02 , 0.025, 0.03 , 0.035, 0.04 , 0.045, 0.05 ]
    deposit_change = [-5. , -4.5, -4. , -3.5, -3. , -2.5, -2. , -1.5, -1. , -0.5,  0. ]

    seeds = random.sample(range(1, 100000), 10000)
    
    deposit = deposit_change[0]
    for cov in cds_covered:
        for naked in cds_naked:
            param = {
                "covered_cds_prob": cov,
                "naked_cds_prob": naked,
                "mu_deposit_growth": deposit
            }
            calibration_variables.update(param)
            results = Parallel(n_jobs=-1)(delayed(run_one_sim)(i,
                                                               copy.deepcopy(bank_data),
                                                               calibration_variables) for i in seeds)
            with open(f"saved_data/results_{cov}_{naked}_{deposit}.pkl", "wb") as f:
                pickle.dump(results, f)
            print(f'success with : covered {cov}, naked {naked}, deposit {deposit}', flush=True)


if __name__ == "__main__":
    main()
