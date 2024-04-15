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
from abm_vec.log import generate_log
from joblib import Parallel, delayed


def run_sim(parameters, bank_data, seeds):
    calibration_variables = get_calibration_variables()
    if parameters is not None:
        calibration_variables.update(parameters)
    if len(seeds) == 1:
        results = run_one_sim(seeds[0], copy.deepcopy(bank_data), calibration_variables)
    else:
        results = Parallel(n_jobs=-1)(delayed(run_one_sim)(i,
                                                           copy.deepcopy(bank_data),
                                                           calibration_variables) for i in seeds)
    return results


def run_one_sim(seed: int, bank_data: dict, calibration_variables: dict):
    """
    | Run the simulation for a given set of parameters and a seed.
    :param seed: Seed to be used for the simulation
    :param bank_data: dictionary with bank data extracted from the Excel file
    :param calibration_variables: dictionary with parameters
    :return:
    """
    results = generate_log()
    results["calibration_variables"] = calibration_variables

    # set seed
    random.seed(seed)
    np.random.seed(seed)
    use_bank_weights = True
    results["seed"] = seed
    results["use_bank_weights"] = use_bank_weights

    # get bank data
    bank_equity = bank_data["equity"]
    bank_deposits = bank_data["deposits"]
    bank_loans = bank_data["loans"]
    results[0]["banks"]["bank_equity"] = bank_equity.copy()
    results[0]["banks"]["bank_deposits"] = bank_deposits.copy()
    results[0]["banks"]["bank_loans"] = bank_loans.copy()

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
    results["bank_weights"] = bank_weights.copy()

    # begin the simulation part
    t = 0
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
    #TODO: remove this
    # results[0]["firms"]["firm_equity"] = firm_equity.copy()
    # results[0]["firms"]["firm_prod"] = firm_prod.copy()
    # results[0]["firms"]["firm_ex_supply"] = firm_ex_supply.copy()
    # results[0]["firms"]["firm_wage"] = firm_wage.copy()
    # results[0]["firms"]["firm_pd"] = firm_pd.copy()
    # results[0]["firms"]["firm_supply"] = firm_supply.copy()
    # results[0]["firms"]["firm_profit"] = firm_profit.copy()
    # results[0]["firms"]["firm_price"] = firm_price.copy()
    # results[0]["firms"]["firm_max_leverage"] = firm_max_leverage.copy()

    # for each firm compute expected supply and see who wants loans
    firm_wage = wages_adj(firm_wage, calibration_variables["min_wage"])
    (
        firm_price,
        firm_supply,
        firm_total_wage,
        supply_threshold_breach,
        min_price_breach
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
    # TODO: remove this
    # results[1]["firms"]["firm_wage"] = firm_wage.copy()
    # results[1]["firms"]["firm_price"] = firm_price.copy()
    # results[1]["firms"]["supply_threshold_breach"] = supply_threshold_breach
    # results[1]["firms"]["firm_credit_demand"] = firm_credit_demand.copy()
    # results[1]["firms"]["firm_financial_fragility"] = firm_financial_fragility.copy()
    # results[1]["firms"]["min_price_breach"] = min_price_breach

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
    results[1]["banks"]["bank_max_credit"] = bank_max_credit.copy()

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
    # results['connections']['possible_loans'] = loans_by_firm.copy()
    # results["connections"]["loan_firms_interest"] = loan_firms_interest.copy()
    # results["connections"]["loan_firms_amount"] = loan_firms_amount.copy()
    # results["connections"]["loan_banks_interest"] = loan_banks_interest.copy()
    # results["connections"]["loan_banks_amount"] = loan_banks_amount.copy()
    # results["connections"]["cds_amount"] = cds_amount.copy()
    # results["connections"]["cds_spread"] = cds_spread.copy()
    # results["connections"]["cds_spread_amount"] = cds_spread_amount.copy()
    results["connections"]["cds_dict"] = cds_dict.copy()
    results[1]["banks"]["bank_loans"] = bank_loan_asset.copy()

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
    # results[1]["firms"]["firm_equity"] = firm_equity.copy()
    # results[1]["firms"]["firm_ex_supply"] = firm_ex_supply.copy()
    # results[1]["firms"]["firm_supply"] = firm_supply.copy()
    # results[1]["firms"]["recovery_rate"] = recovery_rate.copy()
    # results[1]["firms"]["defaulting_firms"] = defaulting_firms.copy()
    # results[1]["firms"]["firm_total_wage"] = firm_total_wage.copy()

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
        liabilities
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
    results[1]["banks"]["bank_equity"] = bank_equity.copy()
    results[1]["banks"]["bank_deposits"] = bank_deposits.copy()
    results[1]["banks"]["defaulted_banks"] = defaulting_banks.copy()
    results[1]["banks"]["liability_matrix"] = liabilities.copy()

    return results
