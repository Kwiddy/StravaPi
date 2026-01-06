#!/usr/bin/env python3
"""
Script to refresh your Strava access token using the refresh token.
This updates your .env file with the new tokens.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def refresh_token():
    """Refresh the access token and update .env file."""
    refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')
    client_id = os.getenv('STRAVA_CLIENT_ID')
    client_secret = os.getenv('STRAVA_CLIENT_SECRET')
    
    if not refresh_token or not client_id or not client_secret:
        print("Error: Missing required tokens in .env file.")
        print("\nYour .env file should contain:")
        print("STRAVA_REFRESH_TOKEN=your_refresh_token")
        print("STRAVA_CLIENT_ID=your_client_id")
        print("STRAVA_CLIENT_SECRET=your_client_secret")
        return False
    
    url = "https://www.strava.com/oauth/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    try:
        print("Refreshing access token...")
        response = requests.post(url, data=data)
        response.raise_for_status()
        result = response.json()
        
        new_access_token = result.get('access_token')
        new_refresh_token = result.get('refresh_token')
        
        if new_access_token:
            print(f"\n✅ Success! New tokens generated:")
            print(f"Access Token: {new_access_token}")
            if new_refresh_token:
                print(f"Refresh Token: {new_refresh_token}")
            
            # Read current .env file
            env_path = '.env'
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    lines = f.readlines()
                
                # Update tokens in .env file
                updated = False
                with open(env_path, 'w') as f:
                    for line in lines:
                        if line.startswith('STRAVA_ACCESS_TOKEN='):
                            f.write(f'STRAVA_ACCESS_TOKEN={new_access_token}\n')
                            updated = True
                        elif line.startswith('STRAVA_REFRESH_TOKEN=') and new_refresh_token:
                            f.write(f'STRAVA_REFRESH_TOKEN={new_refresh_token}\n')
                            updated = True
                        else:
                            f.write(line)
                
                if updated:
                    print(f"\n✅ Updated {env_path} with new tokens!")
                else:
                    print(f"\n⚠️  Could not find STRAVA_ACCESS_TOKEN in {env_path}")
                    print("Please manually update your .env file with:")
                    print(f"STRAVA_ACCESS_TOKEN={new_access_token}")
                    if new_refresh_token:
                        print(f"STRAVA_REFRESH_TOKEN={new_refresh_token}")
            else:
                print(f"\n⚠️  {env_path} file not found. Please manually add:")
                print(f"STRAVA_ACCESS_TOKEN={new_access_token}")
                if new_refresh_token:
                    print(f"STRAVA_REFRESH_TOKEN={new_refresh_token}")
            
            return True
        else:
            print("Error: No access token in response")
            print(f"Response: {result}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return False


if __name__ == "__main__":
    refresh_token()

