#!/usr/bin/env python3
"""
Quick script to add refresh token to .env file.
Uses existing Client ID and Secret from .env, just needs the authorization code.
Usage: python add_refresh_token.py YOUR_AUTHORIZATION_CODE
"""

import sys
import os
import requests
from dotenv import load_dotenv

load_dotenv()

if len(sys.argv) != 2:
    print("Usage: python add_refresh_token.py AUTHORIZATION_CODE")
    print("\nExample:")
    print("python add_refresh_token.py 7d6b2cbb10077c9e1521ed9b28dc1766b7b0c047")
    print("\nTo get the authorization code:")
    client_id = os.getenv('STRAVA_CLIENT_ID', 'YOUR_CLIENT_ID')
    print(f"Visit: https://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri=http://localhost&scope=activity:read_all")
    sys.exit(1)

code = sys.argv[1]
client_id = os.getenv('STRAVA_CLIENT_ID')
client_secret = os.getenv('STRAVA_CLIENT_SECRET')

if not client_id or not client_secret:
    print("Error: STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be in .env file")
    sys.exit(1)

url = "https://www.strava.com/oauth/token"
data = {
    "client_id": client_id,
    "client_secret": client_secret,
    "code": code,
    "grant_type": "authorization_code"
}

try:
    print("Exchanging code for tokens...")
    response = requests.post(url, data=data)
    response.raise_for_status()
    result = response.json()
    
    access_token = result.get('access_token')
    refresh_token = result.get('refresh_token')
    
    if not access_token:
        print("Error: No access token in response")
        print(f"Response: {result}")
        sys.exit(1)
    
    # Update .env file
    env_path = '.env'
    lines = []
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
    
    # Update tokens
    updated_access = False
    updated_refresh = False
    
    with open(env_path, 'w') as f:
        for line in lines:
            if line.startswith('STRAVA_ACCESS_TOKEN='):
                f.write(f'STRAVA_ACCESS_TOKEN={access_token}\n')
                updated_access = True
            elif line.startswith('STRAVA_REFRESH_TOKEN='):
                f.write(f'STRAVA_REFRESH_TOKEN={refresh_token}\n')
                updated_refresh = True
            else:
                f.write(line)
        
        if not updated_access:
            f.write(f'STRAVA_ACCESS_TOKEN={access_token}\n')
        if not updated_refresh and refresh_token:
            f.write(f'STRAVA_REFRESH_TOKEN={refresh_token}\n')
    
    print(f"\n✅ Success! Updated {env_path} with:")
    print(f"   - New Access Token: {access_token[:20]}...")
    if refresh_token:
        print(f"   - Refresh Token: {refresh_token[:20]}...")
    print("\nYour tokens are now set up for automatic refresh!")
    
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
    if hasattr(e, 'response') and e.response:
        print(f"Response: {e.response.text}")
    sys.exit(1)

