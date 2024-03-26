#!/bin/bash
### Here are the SBATCH parameters that you should always consider:
#SBATCH --ntasks=1          ## Not strictly necessary because default is 1
#SBATCH --mem=128000
#SBATCH --time=12:00:00
#SBATCH --output=abmcpu.out	## standard out file
#SBATCH --cpus-per-task=64
module load anaconda3
source activate myenv
srun python main.py