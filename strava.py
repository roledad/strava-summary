"""
Strava API utils
"""

import os
import json
from datetime import datetime
import requests
import pandas as pd


# CONFIGURATION
CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REDIRECT_URI = 'http://localhost/exchange_token'  # Same as registered
SCOPE = 'read,activity:read_all'

# STEP 1: GET AUTHORIZATION URL
def get_authorization_url():
    """Generate Strava OAuth authorization URL."""
    url = (
        f"https://www.strava.com/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&approval_prompt=force"
        f"&scope={SCOPE}"
    )
    return url

# STEP 2: EXCHANGE CODE FOR ACCESS TOKEN
def exchange_code_for_token(auth_code):
    """Exchange authorization code for access token."""
    response = requests.post(
        'https://www.strava.com/oauth/token',
        data={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': auth_code,
            'grant_type': 'authorization_code'
        },
        timeout=30
    )
    token_data = response.json()
    with open('strava_token.json', 'w', encoding='utf-8') as f:
        json.dump(token_data, f)
    return token_data

# STEP 3: REFRESH ACCESS TOKEN IF EXPIRED
def refresh_access_token():
    """Refresh expired access token using refresh token."""
    with open('strava_token.json', encoding='utf-8') as f:
        tokens = json.load(f)

    response = requests.post(
        'https://www.strava.com/oauth/token',
        data={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': tokens['refresh_token']
        },
        timeout=30
    )

    new_tokens = response.json()
    with open('strava_token.json', 'w', encoding='utf-8') as f:
        json.dump(new_tokens, f)
    return new_tokens['access_token']

# STEP 4: GET ATHLETE ACTIVITIES
def get_activities(after=None, before=None, per_page=30):
    """Fetch athlete activities from Strava API."""
    with open('strava_token.json', encoding='utf-8') as f:
        tokens = json.load(f)

    access_token = tokens.get('access_token')

    params = {
        'per_page': per_page,
    }
    if after:
        params['after'] = int(after)
    if before:
        params['before'] = int(before)

    response = requests.get(
        'https://www.strava.com/api/v3/athlete/activities',
        headers={'Authorization': f'Bearer {access_token}'},
        params=params, timeout=30
    )

    if response.status_code == 401:
        print("Access token expired, refreshing...")
        access_token = refresh_access_token()
        return get_activities(after, before, per_page)

    return response.json()

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


def main():
    """read activities"""
    read_date = datetime(2025, 6, 1)
    activities = get_activities(after=read_date.timestamp())
    df = pd.DataFrame(activities)
    print(f"Number of activities after {read_date.date().strftime("%Y-%m-%d")}:", df["type"].value_counts().to_dict())

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

    # Save with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join("data", f"strava_run_data_{timestamp}.csv")
    run_df.to_csv(file_path, index=False)

    # Also save latest version
    run_df.to_csv("strava_run_data.csv", index=False)

    print(f"Data saved: strava_run_data_{timestamp}.csv")
    print("Latest data: strava_run_data.csv")

if __name__ == "__main__":
    main()
