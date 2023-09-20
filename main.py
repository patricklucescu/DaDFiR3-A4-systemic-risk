import pandas as pd

from abm_model import abm_simulation
import multiprocessing
import time
import random
import shelve
import dill as pickle
import pandas
import matplotlib.pyplot as plt
from abm_model.calibration import *

parallel=False
num_iterations = 100
nr_success = 0
rnd_seed = 0
load_module = True
module_name = 'covered05recession10duration10.pkl'
out_name = 'abm_run' + str(round(time.time() * 1000)) + '.pkl'
calibration = get_calibration_variables()

print(f'File: {out_name}', flush=True)
print(f'Calibration: {calibration}', flush=True)


results = {}

if not load_module:
    if parallel:
        if __name__ == "__main__":
            # start = time.time()
            # Number of parallel processes (you can adjust this)
            num_processes = multiprocessing.cpu_count()  # Use all available CPU cores
            # Create a pool of worker processes
            pool = multiprocessing.Pool(processes=num_processes)
            # Use the pool to execute the function in parallel
            tempresults = pool.map(abm_simulation.abm_model, range(num_iterations))
            # Close the pool and wait for the work to finish
            pool.close()
            pool.join()
            # end = time.time()
            # print(f"Finished in {(end - start) / 60} minutes")

            for i in range (num_iterations):
                results.update({i: {'srisk': tempresults[i][0], 'assets': tempresults[i][1]}})

            with open(out_name, 'wb') as file:
                pickle.dump(results, file)

    else:

        # start = time.time()

        while nr_success < num_iterations:

            # abm_simulation.abm_model(random.randint(1,10000))
            try:
                srisk_positive_aggregate, aggregate_assets = abm_simulation.abm_model(rnd_seed)
                nr_success += 1
                results.update({nr_success: {'srisk': srisk_positive_aggregate, 'assets': aggregate_assets}})
                print(f'success seed: {rnd_seed}', flush=True)
                rnd_seed += 1
            except:
                print(f'failed seed: {rnd_seed}', flush=True)
                print(f'failed seed: {rnd_seed}', flush=True)

                rnd_seed += 1

            with open(out_name, 'wb') as file:
                pickle.dump(results, file)



        # end = time.time()
        # print(f"Simulation finished in {(end - start) / 60} minutes")



else:

    with open(module_name, 'rb') as file:
        results = pickle.load(file)

    results.keys()

    aggregate_assets = pd.DataFrame(index=results[1]['assets'].keys())
    aggregate_srisk =  pd.DataFrame(index=results[1]['srisk'].keys())
    for i in results.keys():

        aggregate_assets[i] = results[i]['assets'].values
        aggregate_srisk[i] = results[i]['srisk'].values

    aggregate_srisk_per_assets = aggregate_srisk/aggregate_assets
    avg_aggregate_srisk_per_assets = aggregate_srisk_per_assets.mean(axis=1)
    avg_aggregate_srisk = aggregate_srisk.mean(axis=1)
    avg_aggregate_assets = aggregate_assets.mean(axis=1)

    plt.plot(avg_aggregate_srisk_per_assets*100, color='blue')
    plt.ylabel('Systemic risk in % of aggregate assets', color='blue')
    plt.tick_params(axis='y', labelcolor='blue')
    plt.title("Aggregate systemic risk")
    plt.axvline(x=175, color='r', label='shock')
    plt.axvline(x=185, color='r', label='shock')
    # plt.savefig(str(round(time.time()*1000))+'.pdf')
    plt.show()

    plt.plot(avg_aggregate_srisk, color='blue')
    plt.ylabel('Systemic risk in $', color='blue')
    plt.tick_params(axis='y', labelcolor='blue')
    plt.title("Aggregate systemic risk")
    plt.axvline(x=175, color='r', label='shock')
    plt.axvline(x=185, color='r', label='shock')
    # plt.savefig(str(round(time.time()*1000))+'.pdf')
    plt.show()


    plt.plot(avg_aggregate_assets, color='blue')
    plt.ylabel('Aggregate assets in $', color='blue')
    plt.tick_params(axis='y', labelcolor='blue')
    plt.title("Aggregate assets")
    plt.axvline(x=175, color='r', label='shock')
    plt.axvline(x=185, color='r', label='shock')
    # plt.savefig(str(round(time.time()*1000))+'.pdf')
    plt.show()
