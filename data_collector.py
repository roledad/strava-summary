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

from data import get_run_data, fetch_all_historical_run_data_and_save

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

def collect_and_save_data(all_historical=False):
    """Collect Strava data and save to data folder.

    If all_historical is True, fetches all activities from API and overwrites
    data/strava_run_data.csv (used by cycle distribution plots).
    Otherwise fetches last 30 days and saves timestamped + latest copy.
    """
    try:
        logging.info("Starting data collection...")

        ensure_data_directory()

        if all_historical:
            logging.info("Fetching all historical run data from API...")
            run_df = fetch_all_historical_run_data_and_save()
            logging.info(f"Saved {len(run_df)} runs to data/strava_run_data.csv")
        else:
            read_date = datetime.now() - timedelta(days=30)
            run_df = get_run_data(read_date)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"data/strava_run_data_{timestamp}.csv"
            run_df.to_csv(file_path, index=False)
            run_df.to_csv("data/strava_run_data.csv", index=False)
            logging.info(f"Data saved: {file_path}")
            logging.info(f"Collected {len(run_df)} runs")

        return True

    except Exception as e:
        logging.error(f"Error collecting data: {e}")
        return False

def run_continuous_collection(interval_hours=24):
    """Run data collection continuously with specified interval"""
    logging.info(f"Starting continuous data collection (interval: {interval_hours} hours)")

    # Run initial collection immediately
    logging.info("Running initial data collection...")
    collect_and_save_data()

    while True:
        try:
            # Calculate next run time
            next_run = datetime.now() + timedelta(hours=interval_hours)
            logging.info(f"Next data collection scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

            # Wait for the specified interval
            time.sleep(interval_hours * 3600)

            # Run data collection
            logging.info("Running scheduled data collection...")
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
            logging.error(f"Unexpected error in continuous collection: {e}")
            logging.info("Will retry in 1 hour...")
            time.sleep(3600)  # Wait 1 hour before retry
            continue

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Strava Data Collection Agent")
    parser.add_argument("--once", action="store_true", help="Run data collection once and exit")
    parser.add_argument("--all", action="store_true", dest="all_historical",
                        help="Fetch all historical data and save to data/strava_run_data.csv (for dashboard cycle plots)")
    parser.add_argument("--interval", type=float, default=24, help="Collection interval in hours (default: 24)")
    parser.add_argument("--minutes", type=float, help="Collection interval in minutes (overrides --interval)")

    args = parser.parse_args()

    interval_hours = args.minutes / 60 if args.minutes else args.interval

    if args.once:
        collect_and_save_data(all_historical=args.all_historical)
    else:
        run_continuous_collection(interval_hours)
