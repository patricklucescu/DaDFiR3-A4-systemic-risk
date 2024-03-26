from abm_simulation import run_simulation

from abm_vec.initialization import generate_random_entities, get_bank_data

if __name__ == "__main__":
    # get bank data
    bank_data = get_bank_data()
    # get parameters
    parameters = None
    # run simulation
    run_simulation(1, bank_data, parameters)
