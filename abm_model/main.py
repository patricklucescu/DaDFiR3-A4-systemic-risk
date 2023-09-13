from abm_model import abm_simulation
import multiprocessing
import time

parallel=False
num_iterations = 10

if parallel:

    if __name__ == "__main__":

        start = time.time()

        # Number of parallel processes (you can adjust this)
        num_processes = multiprocessing.cpu_count()  # Use all available CPU cores

        # Create a pool of worker processes
        pool = multiprocessing.Pool(processes=num_processes)

        # Use the pool to execute the function in parallel
        results = pool.map(abm_simulation.abm_model, range(num_iterations))

        # Close the pool and wait for the work to finish
        pool.close()
        pool.join()

        end = time.time()
        print(f"Finished in {(end - start) / 60} minutes")

        # You can now use the results as needed
        print(results)

else:

    start = time.time()

    for i in range(num_iterations):

        abm_simulation.abm_model(i)

    end = time.time()
    print(f"Simulation finished in {(end - start) / 60} minutes")


