#!/bin/bash

#SBATCH --nodes=2
#SBATCH --ntasks=24
#SBATCH --time=06-23   
#SBATCH --partition=shas        
#SBATCH	--qos=long
#SBATCH --output=sample-%j.out


module purge

module load python
module load gcc

#beginning of script

python lhs_ep_model.py

#end of script

