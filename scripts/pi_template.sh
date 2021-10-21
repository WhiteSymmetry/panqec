#!/bin/bash
#SBATCH -N 1
#SBATCH -t ${TIME}
#SBATCH --cpus-per-task=1
#SBATCH --exclusive
#SBATCH --job-name=${NAME}
#SBATCH --array=1-${NARRAY}
#SBATCH -p ${QUEUE}
#SBATCH --output=/home/ehuang1/bn3d/slurm/out/${NAME}_%j.out
set -euxo pipefail

# Variables to change.
trials=${TRIALS}
data_dir=temp/paper/${NAME}
input_dir="$data_dir/inputs"
output_dir="$data_dir/results"
log_dir="$data_dir/logs"
bash_command="bn3d run -f {} -o $output_dir -t $trials"

# Print out the current working directory.
pwd

# Load python and activate the python virtual environment.
module purge
module load python/3.8
source venv/bin/activate

# Create the subdirectories
mkdir -p output_dir
mkdir -p log_dir

# Print out the environmental variables and the time.
printenv
date
n_tasks=$SLURM_ARRAY_TASK_COUNT
i_task=$SLURM_ARRAY_TASK_ID

# Run a CPU and RAM usage logging script in the background.
python scripts/monitor.py "$log_dir/usage_${SLURM_JOB_ID}_${i_task}.txt" &

# Function that prints out filtered functions.
function filter_files() {
    counter=0
    for filename in $input_dir/*.json; do
        if [[ $(( counter % n_tasks + 1 )) == $i_task ]]; then
            echo $filename
        fi
        counter=$(( counter + 1 ))
    done
}

# Run in parallel.
filter_files | parallel --results $log_dir $bash_command :::

# Print out the date when done.
date