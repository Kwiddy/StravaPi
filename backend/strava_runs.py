#!/usr/bin/env python3
"""
Simple script to fetch and display the latest 3 runs from Strava API.
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def refresh_access_token():
    """Refresh the access token using the refresh token and update .env file."""
    refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')
    client_id = os.getenv('STRAVA_CLIENT_ID')
    client_secret = os.getenv('STRAVA_CLIENT_SECRET')
    
    if not refresh_token or not client_id or not client_secret:
        return None
    
    url = "https://www.strava.com/oauth/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        result = response.json()
        
        new_access_token = result.get('access_token')
        new_refresh_token = result.get('refresh_token', refresh_token)  # Use old one if not provided
        
        if new_access_token:
            # Update .env file with new tokens
            env_path = '.env'
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    lines = f.readlines()
                
                with open(env_path, 'w') as f:
                    for line in lines:
                        if line.startswith('STRAVA_ACCESS_TOKEN='):
                            f.write(f'STRAVA_ACCESS_TOKEN={new_access_token}\n')
                        elif line.startswith('STRAVA_REFRESH_TOKEN=') and new_refresh_token:
                            f.write(f'STRAVA_REFRESH_TOKEN={new_refresh_token}\n')
                        else:
                            f.write(line)
            
            print("Token refreshed successfully and saved to .env!")
            return new_access_token, new_refresh_token
        return None, None
    except requests.exceptions.RequestException as e:
        print(f"Error refreshing token: {e}")
        return None, None


def get_access_token():
    """Get access token from .env file, refresh if needed."""
    token = os.getenv('STRAVA_ACCESS_TOKEN')
    if not token:
        print("Error: STRAVA_ACCESS_TOKEN not found in .env file.")
        print("\nTo get your access token:")
        print("1. Go to https://www.strava.com/settings/api")
        print("2. Create an application to get your Client ID and Client Secret")
        print("3. Use an OAuth flow or visit: https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&scope=activity:read_all")
        print("4. Exchange the code for an access token using exchange_token.py")
        print("\nCreate a .env file in the project directory with:")
        print("STRAVA_ACCESS_TOKEN=your_token_here")
        print("STRAVA_REFRESH_TOKEN=your_refresh_token_here")
        print("STRAVA_CLIENT_ID=your_client_id")
        print("STRAVA_CLIENT_SECRET=your_client_secret")
        return None
    return token


def get_activities(access_token, per_page=30):
    """Fetch activities from Strava API."""
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"per_page": per_page}
    
    response = requests.get(url, headers=headers, params=params)
    
    # Check for 401 error before raising
    if response.status_code == 401:
        error_text = response.text if hasattr(response, 'text') else ''
        
        # Try to refresh token on any 401 error (token is likely expired or invalid)
        print("Access token appears to be invalid or expired. Attempting to refresh...")
        new_token, new_refresh = refresh_access_token()
        if new_token:
            # Reload environment variables to get the updated token
            load_dotenv(override=True)
            # Retry the request with new token
            headers = {"Authorization": f"Bearer {new_token}"}
            print("Retrying request with refreshed token...")
            retry_response = requests.get(url, headers=headers, params=params)
            
            if retry_response.status_code == 200:
                return retry_response.json()
            elif retry_response.status_code == 401:
                retry_error_text = retry_response.text if hasattr(retry_response, 'text') else ''
                # Check for permission error after refresh
                if 'activity:read_permission' in retry_error_text or 'activity:read' in retry_error_text:
                    print("\n⚠️  Your access token is missing the 'activity:read_all' scope.")
                    print("\nTo fix this:")
                    print("1. Go to https://www.strava.com/settings/api")
                    print("2. Find your Client ID")
                    print("3. Visit this URL (replace YOUR_CLIENT_ID with your actual Client ID):")
                    print("   https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&scope=activity:read_all")
                    print("4. Authorize the app and copy the 'code' from the redirect URL")
                    print("5. Exchange the code for a new access token with the correct scope")
                print(f"Error after token refresh: {retry_response.status_code}")
                print(f"Response: {retry_error_text}")
        else:
            print("Failed to refresh access token. Please run 'python setup_tokens.py' to set up new tokens.")
        
        # Check for permission error in original error
        if 'activity:read_permission' in error_text or 'activity:read' in error_text:
            print("\n⚠️  Your access token is missing the 'activity:read_all' scope.")
            print("\nTo fix this:")
            print("1. Go to https://www.strava.com/settings/api")
            print("2. Find your Client ID")
            print("3. Visit this URL (replace YOUR_CLIENT_ID with your actual Client ID):")
            print("   https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&scope=activity:read_all")
            print("4. Authorize the app and copy the 'code' from the redirect URL")
            print("5. Exchange the code for a new access token with the correct scope")
        
        print(f"Error fetching activities: 401 Client Error: Unauthorized")
        print(f"Response: {error_text}")
        return None
    
    # For other errors, raise as usual
    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching activities: {e}")
        if hasattr(e, 'response') and e.response and hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None


def filter_runs(activities):
    """Filter activities to only include runs."""
    return [activity for activity in activities if activity.get('type') == 'Run']


def format_duration(seconds):
    """Convert seconds to HH:MM:SS format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_distance(meters):
    """Convert meters to kilometers."""
    return meters / 1000


def display_run(run, index):
    """Display run details in a formatted way."""
    print(f"\n{'='*60}")
    print(f"Run #{index + 1}")
    print(f"{'='*60}")
    
    # Name
    name = run.get('name', 'Untitled Run')
    print(f"Name: {name}")
    
    # Date
    start_date = run.get('start_date_local', '')
    if start_date:
        date_obj = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        print(f"Date: {date_obj.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Distance
    distance = run.get('distance', 0)
    print(f"Distance: {format_distance(distance):.2f} km")
    
    # Duration
    moving_time = run.get('moving_time', 0)
    print(f"Duration: {format_duration(moving_time)}")
    
    # Average pace
    if distance > 0 and moving_time > 0:
        pace_seconds_per_km = moving_time / (distance / 1000)
        pace_min = int(pace_seconds_per_km // 60)
        pace_sec = int(pace_seconds_per_km % 60)
        print(f"Average Pace: {pace_min}:{pace_sec:02d} min/km")
    
    # Elevation
    elevation = run.get('total_elevation_gain', 0)
    if elevation:
        print(f"Elevation Gain: {elevation:.0f} m")
    
    # Average heart rate (if available)
    if 'average_heartrate' in run and run['average_heartrate']:
        print(f"Average Heart Rate: {run['average_heartrate']:.0f} bpm")
    
    # Description (if available)
    description = run.get('description', '')
    if description:
        print(f"Description: {description}")


def main():
    """Main function to fetch and display runs."""
    print("Fetching your latest runs from Strava...")
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        return
    
    # Fetch activities
    activities = get_activities(access_token)
    if activities is None:
        return
    
    # Filter for runs
    runs = filter_runs(activities)
    
    if not runs:
        print("\nNo runs found in your recent activities.")
        return
    
    # Get latest 3 runs
    latest_runs = runs[:3]
    
    print(f"\nFound {len(runs)} run(s). Displaying latest 3:\n")
    
    # Display each run
    for i, run in enumerate(latest_runs):
        display_run(run, i)
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()

