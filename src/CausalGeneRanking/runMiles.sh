#!/bin/bash
#$ -V
#$ -S /bin/bash
#$ -cwd
#$ -m as
#$ -M m.m.nieboer@umcutrecht.nl
#$ -l h_vmem=25G
#$ -l h_rt=48:00:00
#$ -e miles_lasso2Patients_random_err
#$ -o miles_lasso2Patients_random_out

python milesAllBags.py