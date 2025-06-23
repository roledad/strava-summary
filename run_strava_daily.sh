#!/bin/bash

# Change to the script directory
cd "$(dirname "$0")"

# Activate virtual environment if you have one
source ~/utils/miniforge3/bin/activate
conda activate sklearn_env

# Run the Strava script
python strava.py

# Optional: Add timestamp to log
echo "$(date): Strava data updated" >> strava_daily.log