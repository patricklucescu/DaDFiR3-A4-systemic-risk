def get_calibration_variables():
    """
    | Generate the calibration variables.

    :return: the calibration variables
    """

    calibration_variables = {}
    # agents and time periods
    calibration_variables.update({"FIRMS": 10000})
    calibration_variables.update({"T": 1})
    # CDS
    calibration_variables.update({"covered_cds_prob": 0.0})
    calibration_variables.update({"naked_cds_prob": 0.00})
    calibration_variables.update({"cds_fractional": 1})
    # Base agent
    calibration_variables.update({"policy_rate": 0.025})
    calibration_variables.update({"max_bank_loan": 5})
    calibration_variables.update({"max_interbank_loan": 3})
    calibration_variables.update({"max_cds_requests": 3})
    # Base-Bank
    calibration_variables.update({"h_theta": 0.1})
    # Banks
    calibration_variables.update({"capital_req": 0.85})
    calibration_variables.update({"mu_deposit_growth": 0.0})
    calibration_variables.update({"std_deposit_growth": 3})
    # Base-Firm
    calibration_variables.update({"min_productivity": 1.40844727 * 10 ** 2})
    calibration_variables.update({"min_wage": 80000})
    calibration_variables.update({"min_max_leverage": 2})
    calibration_variables.update({"max_max_leverage": 15})
    calibration_variables.update({"leverage_severity": 0.30})
    calibration_variables.update({"market_price": 600})
    # calibration_variables.update(
    #     {
    #         "market_price": (1 + calibration_variables["policy_rate"])
    #         * calibration_variables["min_wage"]
    #         / calibration_variables["min_productivity"]
    #     }
    # )

    # Firms
    calibration_variables.update({"firm_equity_poisson_lambda": 4})
    calibration_variables.update({"firm_equity_scaling": 10000})
    calibration_variables.update({"firm_supply_poisson_lambda": 4})
    calibration_variables.update({"firm_supply_scaling": 200000})
    calibration_variables.update({"firm_init_excess_supply_prob": 0.25})
    # firm equity and supply generation via copula
    calibration_variables.update({"firm_rho": 0.937765503})
    calibration_variables.update({"firm_lb1": 9.87030029 * 10 ** 5})
    calibration_variables.update({"firm_lb2": 7.81471252 * 10 ** 3})
    calibration_variables.update({"firm_ub1": 1.51020813 * 10 ** 8})
    calibration_variables.update({"firm_ub2": 6.98611450 * 10 ** 5})
    calibration_variables.update({"firm_alpha1": 1.66713867})
    calibration_variables.update({"firm_alpha2": 1.66508484e+00})

    # Markov Model states
    calibration_variables.update({"markov_model_states": [1]})
    assert (
        len(calibration_variables["markov_model_states"]) == calibration_variables["T"]
    ), "Markov model economy states should be same length as the number of time steps to simulate"
    calibration_variables.update({"good_consumption": [0.88, 0.83]})
    calibration_variables.update({"good_consumption_std": [0.01, 0.01]})
    calibration_variables.update({"min_consumption": 0.7})
    calibration_variables.update({"max_consumption": 1})

    return calibration_variables
