"""Process Strava data"""

import os
from datetime import datetime, timedelta
import pandas as pd
from strava import get_activities

# HELPER FUNCTIONS
def decimal_to_time(decimal_time):
    """Convert decimal minutes to MM:SS format."""
    minutes = int(decimal_time)
    seconds = int((decimal_time - minutes) * 60)
    return f"{minutes}:{seconds:02d}"

def time_to_decimal(time_str):
    """Convert MM:SS format to decimal minutes."""
    minutes, seconds = map(int, time_str.split(':'))
    return minutes + seconds / 60

def get_data(read_date=None):
    """Get the data"""
    if read_date is None:
        read_date = datetime.now() - timedelta(days=30)
    activities = get_activities(after=read_date.timestamp())
    df = pd.DataFrame(activities)
    read_date_str = read_date.date().strftime("%Y-%m-%d")
    print(f"Number of activities after {read_date_str}:", df["type"].value_counts().to_dict())
    return df

def get_run_data(read_date=None):
    """Get the run data"""
    df = get_data(read_date)

    map_df = pd.DataFrame(df[df["type"].isin(["Ride", "Run"])]["map"].tolist())
    map_df["id"] = map_df["id"].str.replace("a", "").astype(int)

    cols = [
        "id", "sport_type", "name", "visibility", "start_date_local",
        "distance", "moving_time", "elapsed_time", "average_speed", "average_cadence",
        "total_elevation_gain", "elev_high", "elev_low",
        "average_heartrate", "max_heartrate", "average_watts", "max_watts",
        "weighted_average_watts", "kilojoules"
    ]
    run_df = pd.merge(pd.DataFrame(df[df["type"]=="Run"][cols]), map_df, on="id", how="left")
    run_df["start_date_local"] = pd.to_datetime(run_df["start_date_local"])
    run_df['distance_mile'] = run_df['distance'] / 1609.34
    run_df['moving_time_minute'] = run_df['moving_time'] / 60
    run_df['pace'] = run_df['moving_time_minute'] / run_df['distance_mile']
    run_df["total_elevation_gain_ft"] = run_df["total_elevation_gain"] * 3.28084
    run_df['pace'] = run_df['pace'].apply(decimal_to_time)
    run_df["week"] = pd.to_datetime(run_df["start_date_local"]).dt.isocalendar().week
    run_df["weekly_milages_cumsum"] = run_df.groupby("week")["distance_mile"].cumsum().round(2)

    return run_df

def get_summary_stats(run_df):
    """Calculate summary statistics for the run data"""
    start_date = pd.to_datetime(run_df['start_date_local']).min().date().strftime("%Y-%m-%d")
    end_date = pd.to_datetime(run_df['start_date_local']).max().date().strftime("%Y-%m-%d")
    # Calculate summary statistics
    summary_stats = {
        'Time Period': f"{start_date} ~ {end_date}",
        'Number of Runs': len(run_df),
        'Total Distance (miles)': run_df['distance_mile'].sum(),
        'Total Moving Time (hours)': run_df['moving_time_minute'].sum() / 60,
        'Total Elevation Gain (ft)': run_df['total_elevation_gain_ft'].sum(),
        'Average Pace (min/mile)': decimal_to_time(run_df['pace'].apply(time_to_decimal).mean()),
        'Average Heart Rate (bpm)': run_df['average_heartrate'].mean(),
        'Average Watts': run_df['average_watts'].mean()
    }

    return summary_stats

def main():
    """Main function"""
    read_date = datetime(2025, 6, 1)
    run_df = get_run_data(read_date)
    # Save with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join("data", f"strava_run_data_{timestamp}.csv")
    run_df.to_csv(file_path, index=False)

    # Also save latest version
    file_path = os.path.join("data", "strava_run_data.csv")
    run_df.to_csv("strava_run_data.csv", index=False)

    print(f"Data saved: strava_run_data_{timestamp}.csv")
    print("Latest data: strava_run_data.csv")

if __name__ == "__main__":
    main()
