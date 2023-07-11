import numpy as np
from scipy.stats import poisson

def get_calibration_variables():

    calibration_variables = {}

    #agents and time periods
    calibration_variables.update({'FIRMS' : 300})
    calibration_variables.update({'BANKS': 20})
    calibration_variables.update({'T' : 200})

    #CDS
    calibration_variables.update({'covered_cds_prob': 0.5})
    calibration_variables.update({'naked_cds_prob': 0.0})

    #Markov Model
    calibration_variables.update({'transition_matrix': np.array([[0.7, 0.3], [0.8, 0.2]])})
    calibration_variables.update({'good_consumption': [0.95, 0.90]})
    calibration_variables.update({'good_consumption_std': [0.1, 0.15]})
    calibration_variables.update({'min_consumption': 0.85})
    calibration_variables.update({'max_consumption': 1})
    calibration_variables.update({'starting_prob': [1, 0]})
    calibration_variables.update({'states': {0: 'good', 1: 'bad'}})

    #Base agent
    calibration_variables.update({'policy_rate': 0.02})
    calibration_variables.update({'max_bank_loan': 3})
    calibration_variables.update({'max_interbank_loan': 3})
    calibration_variables.update({'max_cds_requests': 3})

    #Base-Firm
    calibration_variables.update({'min_productivity': 0.3})
    calibration_variables.update({'min_wage': 200})
    calibration_variables.update({'min_max_leverage': 3})
    calibration_variables.update({'max_max_leverage': 15})
    calibration_variables.update({'leverage_severity': 0.2})

    #Firms
    calibration_variables.update({'firm_equity_poisson_lambda': 4})
    calibration_variables.update({'firm_equity_scaling': 500000})
    calibration_variables.update({'firm_supply_poisson_lambda': 4})
    calibration_variables.update({'firm_supply_scaling': 300000})
    calibration_variables.update({'firm_init_excess_supply_prob': 0.3})

    #Base-Bank
    calibration_variables.update({'h_theta': 0.1})

    #Banks
    calibration_variables.update({'capital_req': 0.9})
    calibration_variables.update({'bank_equity_scaling': 1000000})
    calibration_variables.update({'bank_supply_poisson_lambda': 4})
    calibration_variables.update({'min_deposit_ratio': 5})
    calibration_variables.update({'max_deposit_ratio': 12})

    return calibration_variables

def anaylse_calibration(calibration_variables, firms, banks):

    # #analyze and print calibration results

    expected_firm_equity = calibration_variables['FIRMS'] * (calibration_variables['firm_equity_scaling'] *
                                                             calibration_variables['firm_equity_poisson_lambda'] + poisson.pmf(0,calibration_variables['firm_equity_poisson_lambda'])
                                                             * 0.5 * calibration_variables['firm_equity_scaling'])
    # expected_bank_equity =
    # expected_bank_deposits =
    # expected_firm_supply =
    # expected_firm_wage =
    # expected_loan_demand =

    actual_firm_equity = sum([firms[firm_id].equity for firm_id in firms])
    # actual_bank_equity =
    # actual_bank_deposits =
    # actual_firm_supply =
    # actual_firm_wage =
    # actual_loan_demand =

    print(f'expected firm equity: {expected_firm_equity}, actual firm equity: {actual_firm_equity}, deviation: {(expected_firm_equity-actual_firm_equity)/expected_firm_equity}')

    return