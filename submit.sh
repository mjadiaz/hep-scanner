#!/bin/bash 
#SBATCH --job-name=THDM
#SBATCH --time=6:00:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=40

source /home/mjad1g20/.bashrc
source activate rrlib

#python run_scan.py
#python scan_diphoton_paper.py
#python run_scan_mssm.py
python run_scan_thdm.py
