#!/bin/bash 
#SBATCH --job-name=Scan
#SBATCH --time=12:00:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=40

source /home/mjad1g20/.bashrc
source activate rrlib

python run_scan.py

