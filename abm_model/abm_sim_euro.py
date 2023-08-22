import copy
import time
from abm_model.euro_bank_initialize import generate_random_entities  #, generate_new_entities
from abm_model.essentials import merge_dict
from abm_model.analytics import *
from abm_model.markov_model import MarkovModel
from abm_model.clear_interbank_market import clear_interbank_market
from abm_model.clear_firm_default import clear_firm_default
from abm_model.create_network_connections import create_network_connections
from abm_model.logs import LogMessage
from abm_model.calibration import *
import itertools
import numpy as np


calibration_variables = get_calibration_variables()

#assign variables
FIRMS = calibration_variables['FIRMS']
T = calibration_variables['T']
covered_cds_prob = calibration_variables['covered_cds_prob']
naked_cds_prob = calibration_variables['naked_cds_prob']


# generate unique indices for the firms and banks
firms_idx = [f'firm_{x}' for x in range(1, FIRMS + 1)]
firms, banks, base_agent, base_firm, base_bank = generate_random_entities(firms_idx, calibration_variables)

# create logs and initialize historic values
logs = []
historic_data = {}

# begin the simulation part
for t in range(T):
    # for each firm compute expected supply and see who wants loans
    print(f"Period {t}: Compute expected supply and price")
    for firm_id in firms.keys():
        firms[firm_id].compute_expected_supply_and_prices()
        firms[firm_id].check_loan_desire_and_choose_loans()

    # iterate through banks and see which ones accept the loans
    loan_requests = merge_dict(
        list(itertools.chain(*[[{loan.lender: loan} for loan in firms[firm_id].potential_lenders]
                               for firm_id in firms.keys()])))