import numpy as np
from numpy import ndarray


def clear_firm_default(
    loan_firms_interest: ndarray,
    loan_firms_amount: ndarray,
    firm_equity: ndarray,
    firm_total_wage: ndarray,
    firm_supply: ndarray,
    firm_prod: ndarray,
    firm_wage: ndarray,
    calibration_variables: dict,
    num_firms: int,
    firm_price: int,
    economy_state: int,
) -> tuple:
    """
    | This function clears the defaulting firms and updates the equity of the firms

    :param loan_firms_interest: Matrix of loans interest from each firm to each other bank
    :param loan_firms_amount: Matrix of loans amounts from each firm to each other bank
    :param firm_equity: Vector of equity of each firm
    :param firm_total_wage: Vector of total wages paid by each firm
    :param firm_supply: Vector of supply of each firm
    :param firm_prod: Vector of production of each firm
    :param firm_wage: Vector of wages paid by each firm
    :param calibration_variables: Calibration variables
    :param num_firms: Number of firms
    :param firm_price: Vector of prices of each firm
    :param economy_state: The economy state
    :return:
    """
    # set consumption for economy state
    consumption = calibration_variables["good_consumption"][economy_state]
    consumption_std = calibration_variables["good_consumption_std"][economy_state]
    # adjust_production
    condition = firm_total_wage > firm_equity
    firm_total_wage = np.where(condition, firm_equity, firm_total_wage)
    firm_supply = np.where(condition, firm_equity * firm_prod / firm_wage, firm_supply)
    # produce_supply_consumption
    firm_prev_equity = firm_equity.copy()
    firm_equity = firm_equity - firm_total_wage
    actual_consumption_percentage = np.minimum(
        np.maximum(
            calibration_variables["min_consumption"],
            np.random.normal(
                consumption,
                consumption_std,
                num_firms,
            ),
        ),
        calibration_variables["max_consumption"],
    )
    firm_equity += firm_price * actual_consumption_percentage * firm_supply
    firm_ex_supply = (1 - actual_consumption_percentage) * firm_supply

    # figure out who defaulted
    loan_firm_value = (1 + loan_firms_interest) * loan_firms_amount
    firm_loan_owed = np.sum(loan_firm_value, axis=1)
    defaulting_firms = np.where(firm_equity < firm_loan_owed)[0]
    recovery_rate = np.ones(num_firms)
    recovery_rate[defaulting_firms] = (
        firm_equity[defaulting_firms] / firm_loan_owed[defaulting_firms]
    )
    loan_firm_value = recovery_rate[:, np.newaxis] * loan_firm_value
    firm_equity -= recovery_rate * firm_loan_owed

    return (
        firm_equity,
        firm_ex_supply,
        firm_supply,
        firm_prev_equity,
        recovery_rate,
        loan_firm_value,
        defaulting_firms,
        firm_total_wage,
    )
