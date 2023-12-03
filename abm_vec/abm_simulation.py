import numpy as np
import random
from abm_vec.calibration import get_calibration_variables
from abm_vec.initialization import generate_random_entities
from abm_vec.essentials import wages_adj, compute_expected_supply_price
from abm_vec.firms import (
    check_loan_desire_and_choose_loans,
    get_non_zero_values_from_matrix,
    shuffle_firms,
)
from abm_vec.banks import asses_loan_requests_firms
from abm_vec.create_network_connections import create_network_connections
from abm_vec.clear_firm_default import clear_firm_default
from abm_vec.clear_interbank_market import clear_interbank_market

seed_value = 0
random.seed(seed_value)
np.random.seed(seed_value)
use_bank_weights = True
# get calibration variables for initialization and markov model
calibration_variables = get_calibration_variables()

(
    bank_equity,
    bank_deposits,
    bank_loans,
    bank_t1_cap,
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
    bank_weights = np.array([1/num_banks] * num_banks)
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
    # for each firm compute expected supply and see who wants loans
    firm_wage = wages_adj(firm_wage, calibration_variables["min_wage"])
    firm_price, firm_supply, firm_total_wage, supply_threshold_breach = compute_expected_supply_price(
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
    )

    firm_credit_demand = np.maximum(0, firm_total_wage - firm_equity)
    firm_financial_fragility = firm_credit_demand / firm_equity
    loan_indicator = check_loan_desire_and_choose_loans(
        firm_credit_demand, num_firms, num_banks, calibration_variables["max_bank_loan"], bank_weights
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
    #notice that we do not have any interbank loans. Probably because there are too many deposits in relation to loan demand
    (loan_firms_interest,
     loan_firms_amount,
     loan_banks_interest,
     loan_banks_amount,
     cds_amount,
     cds_spread,
     cds_spread_amount,
     bank_current_deposit,
     firm_equity,
     cds_dict,
     bank_loan_asset
     ) = create_network_connections(loans_by_firm,
                                    calibration_variables,
                                    num_firms,
                                    num_banks,
                                    firm_credit_demand,
                                    bank_max_credit,
                                    bank_deposits,
                                    bank_current_deposit,
                                    firm_equity,
                                    firm_pd,
                                    bank_equity)
    # change market price
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
        firm_total_wage
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
        calibration_variables["markov_model_states"][t]
    )

    # do deposit change
    rv = np.random.normal(calibration_variables['mu_deposit_growth'],
                          calibration_variables['std_deposit_growth'],
                          num_banks) / 100
    deposit_change = rv * bank_deposits
    bank_deposits += deposit_change

    # clear interbank market
    (defaulting_banks,
     bank_equity,
     bank_deposits,
     ) = clear_interbank_market(num_banks,
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
                                cds_dict)


