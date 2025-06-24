#!/usr/bin/env python3
"""
Data collection agent for Strava data
Runs periodically to collect and save Strava activity data
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data import get_run_data, main as collect_data

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strava_daily.log'),
        logging.StreamHandler()
    ]
)

def ensure_data_directory():
    """Ensure the data directory exists"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir

def collect_and_save_data():
    """Collect Strava data and save to data folder"""
    try:
        logging.info("Starting data collection...")

        # Ensure data directory exists
        ensure_data_directory()

        # Collect data for the last 30 days by default
        read_date = datetime.now() - timedelta(days=30)
        run_df = get_run_data(read_date)

        # Save with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"data/strava_run_data_{timestamp}.csv"
        run_df.to_csv(file_path, index=False)

        # Also save latest version
        run_df.to_csv("data/strava_run_data.csv", index=False)

        logging.info(f"Data saved: {file_path}")
        logging.info(f"Latest data: data/strava_run_data.csv")
        logging.info(f"Collected {len(run_df)} runs")

        return True

    except Exception as e:
        logging.error(f"Error collecting data: {e}")
        return False

def run_continuous_collection(interval_hours=24):
    """Run data collection continuously with specified interval"""
    logging.info(f"Starting continuous data collection (interval: {interval_hours} hours)")

    while True:
        try:
            success = collect_and_save_data()
            if success:
                logging.info(f"Data collection completed successfully. Next run in {interval_hours} hours.")
            else:
                logging.warning("Data collection failed. Will retry in 1 hour.")
                time.sleep(3600)  # Wait 1 hour before retry
                continue

        except KeyboardInterrupt:
            logging.info("Data collection stopped by user")
            break
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            time.sleep(3600)  # Wait 1 hour before retry
            continue

        # Wait for next collection cycle
        time.sleep(interval_hours * 3600)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Strava Data Collection Agent")
    parser.add_argument("--once", action="store_true", help="Run data collection once and exit")
    parser.add_argument("--interval", type=int, default=24, help="Collection interval in hours (default: 24)")

    args = parser.parse_args()
    if args.once:
        collect_and_save_data()
    else:
        run_continuous_collection(args.interval)
