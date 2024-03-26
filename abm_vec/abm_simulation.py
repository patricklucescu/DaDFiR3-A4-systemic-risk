import copy
import random

import numpy as np

from abm_vec.banks import asses_loan_requests_firms
from abm_vec.calibration import get_calibration_variables
from abm_vec.clear_firm_default import clear_firm_default
from abm_vec.clear_interbank_market import clear_interbank_market
from abm_vec.compute_expected_supply_price import compute_expected_supply_price
from abm_vec.create_network_connections import create_network_connections
from abm_vec.essentials.market_adjustments import wages_adj
from abm_vec.firms import (
    check_loan_desire_and_choose_loans,
    get_non_zero_values_from_matrix,
    shuffle_firms,
)
from abm_vec.initialization import generate_random_entities

# def run_sim(parameters):
#     calibration_variables = get_calibration_variables()
#     if parameters is not None:
#         calibration_variables.update(parameters)


def run_one_sim(seed: int, bank_data: dict, calibration_variables: dict):
    """
    | Run the simulation for a given set of parameters and a seed.
    :param seed: Seed to be used for the simulation
    :param bank_data: dictionary with bank data extracted from the Excel file
    :param calibration_variables: dictionary with parameters
    :return:
    """
    results = {
        "seed": seed,
        "use_bank_weights": True,
        "calibration_variables": calibration_variables,
        "bank_weights": None,
        "start_period": None,
        "end_period": None,
    }

    random.seed(seed)
    np.random.seed(seed)
    use_bank_weights = True

    # get bank data
    bank_equity = bank_data["equity"]
    bank_deposits = bank_data["deposits"]
    bank_loans = bank_data["loans"]
    # bank_t1_cap = bank_data['t1_cap']

    (
        firm_equity,
        firm_prod,
        firm_ex_supply,
        firm_wage,
        firm_pd,
        firm_supply,
        firm_profit,
        firm_price,
        firm_max_leverage,
    ) = generate_random_entities(calibration_variables)

    num_firms = len(firm_price)
    num_banks = len(bank_loans)

    if use_bank_weights:
        bank_weights = bank_loans / sum(bank_loans)
    else:
        bank_weights = np.array([1 / num_banks] * num_banks)
    results["bank_weights"] = bank_weights

    # begin the simulation part
    for t in range(calibration_variables["T"]):
        # store prior period equity
        prior_period_equity = bank_equity.copy()
        # shuffle firms
        (
            firm_equity,
            firm_prod,
            firm_ex_supply,
            firm_wage,
            firm_pd,
            firm_supply,
            firm_profit,
            firm_price,
            firm_max_leverage,
        ) = shuffle_firms(
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
        )
        # store start of info
        old_firm_price = copy.deepcopy(firm_price)
        # for each firm compute expected supply and see who wants loans
        firm_wage = wages_adj(firm_wage, calibration_variables["min_wage"])
        (
            firm_price,
            firm_supply,
            firm_total_wage,
            supply_threshold_breach,
        ) = compute_expected_supply_price(
            firm_ex_supply,
            firm_supply,
            firm_price,
            calibration_variables["market_price"],
            firm_wage,
            firm_prod,
            calibration_variables["firm_init_excess_supply_prob"],
            firm_profit,
            firm_max_leverage,
            firm_equity,
            calibration_variables["policy_rate"],
        )

        firm_credit_demand = np.maximum(0, firm_total_wage - firm_equity)
        firm_financial_fragility = firm_credit_demand / firm_equity
        loan_indicator = check_loan_desire_and_choose_loans(
            firm_credit_demand,
            num_firms,
            num_banks,
            calibration_variables["max_bank_loan"],
            bank_weights,
        )

        # let bank give interest rates
        bank_current_deposit = bank_deposits.copy()
        bank_max_credit = bank_deposits / calibration_variables["capital_req"]
        firm_interest = asses_loan_requests_firms(
            loan_indicator,
            firm_credit_demand,
            bank_max_credit,
            firm_pd,
            firm_financial_fragility,
            calibration_variables["policy_rate"],
            calibration_variables["h_theta"],
        )

        # get loans by firm
        loans_by_firm = get_non_zero_values_from_matrix(firm_interest)

        # compute network connections
        # notice that we do not have any interbank loans.
        # Probably because there are too many deposits in relation to loan demand
        (
            loan_firms_interest,
            loan_firms_amount,
            loan_banks_interest,
            loan_banks_amount,
            cds_amount,
            cds_spread,
            cds_spread_amount,
            bank_current_deposit,
            firm_equity,
            cds_dict,
            bank_loan_asset,
        ) = create_network_connections(
            loans_by_firm,
            calibration_variables,
            num_firms,
            num_banks,
            firm_credit_demand,
            bank_max_credit,
            bank_deposits,
            bank_current_deposit,
            firm_equity,
            firm_pd,
            bank_equity,
        )
        # change market price
        old_price = copy.deepcopy(calibration_variables["market_price"])
        calibration_variables["market_price"] = np.average(firm_price)

        # Figure out firm default and update CDS recovery rate accordingly
        (
            firm_equity,
            firm_ex_supply,
            firm_supply,
            firm_prev_equity,
            recovery_rate,
            loan_firm_value,
            defaulting_firms,
            firm_total_wage,
        ) = clear_firm_default(
            loan_firms_interest,
            loan_firms_amount,
            firm_equity,
            firm_total_wage,
            firm_supply,
            firm_prod,
            firm_wage,
            calibration_variables,
            num_firms,
            firm_price,
            calibration_variables["markov_model_states"][t],
        )

        # do deposit change
        rv = (
            np.random.normal(
                calibration_variables["mu_deposit_growth"],
                calibration_variables["std_deposit_growth"],
                num_banks,
            )
            / 100
        )
        deposit_change = rv * bank_deposits
        bank_deposits += deposit_change

        # clear interbank market
        (
            defaulting_banks,
            bank_equity,
            bank_deposits,
        ) = clear_interbank_market(
            num_banks,
            loan_banks_interest,
            loan_banks_amount,
            recovery_rate,
            defaulting_firms,
            loan_firm_value,
            bank_equity,
            deposit_change,
            bank_deposits,
            bank_current_deposit,
            cds_spread_amount,
            cds_dict,
        )
        return (
            bank_loans / prior_period_equity,
            bank_loan_asset / prior_period_equity,
            len(defaulting_banks),
            len(defaulting_firms),
            firm_price,
            old_price,
            old_firm_price,
            calibration_variables["market_price"],
        )
