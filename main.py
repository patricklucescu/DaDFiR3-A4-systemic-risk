import pandas as pd

from abm_model import abm_simulation
import multiprocessing
import time
import random
import shelve
import dill as pickle
import pandas
import matplotlib.pyplot as plt

parallel=False
num_iterations = 20
load_module = True


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
            results = pool.map(abm_simulation.abm_model, range(num_iterations))
            # Close the pool and wait for the work to finish
            pool.close()
            pool.join()
            # end = time.time()
            # print(f"Finished in {(end - start) / 60} minutes")
            with open('abm_run'+str(round(time.time()*1000))+'.pkl', 'wb') as file:
                pickle.dump(results, file)

    else:

        # start = time.time()

        for i in range(num_iterations):

            # abm_simulation.abm_model(random.randint(1,10000))
            srisk_positive_aggregate, aggregate_assets = abm_simulation.abm_model(i)
            results.update({i: {'srisk':srisk_positive_aggregate,'assets':aggregate_assets}})

        # end = time.time()
        # print(f"Simulation finished in {(end - start) / 60} minutes")

    with open('abm_run'+str(round(time.time()*1000))+'.pkl', 'wb') as file:
        pickle.dump(results, file)

else:

    with open('abm_run.pkl', 'rb') as file:
        results = pickle.load(file)

    aggregate_assets = pd.DataFrame(index=results[0]['assets'].keys())
    aggregate_srisk =  pd.DataFrame(index=results[0]['srisk'].keys())
    for i in results.keys():

        aggregate_assets[i] = results[i]['assets'].values
        aggregate_srisk[i] = results[i]['srisk'].values

    aggregate_srisk_per_assets = aggregate_srisk/aggregate_assets
    avg_aggregate_srisk_per_assets = aggregate_srisk_per_assets.mean(axis=1)
    avg_aggregate_srisk = aggregate_srisk.mean(axis=1)
    avg_aggregate_assets = aggregate_assets.mean(axis=1)

    plt.plot(avg_aggregate_srisk_per_assets, color='blue')
    plt.ylabel('Systemic risk in % of aggregate assets', color='blue')
    plt.tick_params(axis='y', labelcolor='blue')
    plt.title("Aggregate systemic risk")
    plt.axvline(x=175, color='r', label='shock')
    # plt.savefig(str(round(time.time()*1000))+'.pdf')
    plt.show()

    plt.plot(avg_aggregate_srisk, color='blue')
    plt.ylabel('Systemic risk in $', color='blue')
    plt.tick_params(axis='y', labelcolor='blue')
    plt.title("Aggregate systemic risk")
    plt.axvline(x=175, color='r', label='shock')
    # plt.savefig(str(round(time.time()*1000))+'.pdf')
    plt.show()


    plt.plot(avg_aggregate_assets, color='blue')
    plt.ylabel('Aggregate assets in $', color='blue')
    plt.tick_params(axis='y', labelcolor='blue')
    plt.title("Aggregate assets")
    plt.axvline(x=175, color='r', label='shock')
    # plt.savefig(str(round(time.time()*1000))+'.pdf')
    plt.show()
