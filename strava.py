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
    all_activities = []
    page = 1
    while True:
        params = {'per_page': per_page, 'page': page}
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
            continue  # retry with new token
        activities = response.json()
        if not activities:
            break
        all_activities.extend(activities)
        if len(activities) < per_page:
            break
        page += 1
    return all_activities

def main():
    """read activities"""
    read_date = datetime(2025, 6, 1)
    activities = get_activities(after=read_date.timestamp())
    df = pd.DataFrame(activities)
    read_date_str = read_date.date().strftime("%Y-%m-%d")
    print(f"Number of activities after {read_date_str}:", df["type"].value_counts().to_dict())

if __name__ == "__main__":
    main()
