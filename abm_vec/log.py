def generate_log():
    log_info = {
        "seed": None,  # done
        "use_bank_weights": None,  # done
        "bank_weights": None,  # done
        "calibration_variables": None,  # done
        0: {
            "banks": {
                "bank_equity": None,  # done
                "bank_deposits": None,  # done
                "bank_loans": None,  # done
            },
            "firms": {
                "firm_equity": None,  # done
                "firm_prod": None,  # done
                "firm_ex_supply": None,  # done
                "firm_wage": None,  # done
                "firm_pd": None,  # done
                "firm_supply": None,  # done
                "firm_profit": None,  # done
                "firm_price": None,  # done
                "firm_max_leverage": None,  # done
            },
        },
        1: {
            "banks": {
                "bank_equity": None,
                "bank_deposits": None,
                "bank_loans": None,
                "defaulted_banks": None,
                "bank_max_credit": None,
            },
            "firms": {
                "firm_equity": None,
                "firm_ex_supply": None,
                "recovery_rate": None,
                "defaulting_firms": None,
                "firm_wage": None,
                "firm_price": None,
                "firm_supply": None,
                "firm_total_wage": None,
                "firm_credit_demand": None,
                "firm_financial_fragility": None,
                "supply_threshold_breach": None,
                "min_price_breach": None
            },
        },
        "connections": {
            "loan_firms_interest": None,
            "loan_firms_amount": None,
            "loan_banks_interest": None,
            "loan_banks_amount": None,
            "cds_amount": None,
            "cds_spread": None,
            "cds_spread_amount": None,
            "cds_dict": None,
        },
    }
    return log_info
