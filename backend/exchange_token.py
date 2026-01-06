#!/usr/bin/env python3
"""
Quick script to exchange authorization code for access token.
Usage: python exchange_token.py YOUR_CLIENT_ID YOUR_CLIENT_SECRET YOUR_CODE
"""

import sys
import requests

if len(sys.argv) != 4:
    print("Usage: python exchange_token.py CLIENT_ID CLIENT_SECRET CODE")
    print("\nExample:")
    print("python exchange_token.py 12345 secret123 7d6b2cbb10077c9e1521ed9b28dc1766b7b0c047")
    sys.exit(1)

client_id = sys.argv[1]
client_secret = sys.argv[2]
code = sys.argv[3]

url = "https://www.strava.com/oauth/token"
data = {
    "client_id": client_id,
    "client_secret": client_secret,
    "code": code,
    "grant_type": "authorization_code"
}

try:
    print("Exchanging code for access token...")
    response = requests.post(url, data=data)
    response.raise_for_status()
    result = response.json()
    
    access_token = result.get('access_token')
    refresh_token = result.get('refresh_token')
    
    if access_token:
        print(f"\n✅ Success! Your tokens are:")
        print(f"\nAccess Token: {access_token}")
        if refresh_token:
            print(f"Refresh Token: {refresh_token}\n")
        print("Add these to your .env file:")
        print(f"STRAVA_ACCESS_TOKEN={access_token}")
        if refresh_token:
            print(f"STRAVA_REFRESH_TOKEN={refresh_token}")
            print(f"STRAVA_CLIENT_ID={client_id}")
            print(f"STRAVA_CLIENT_SECRET={client_secret}")
            print("\nNote: The refresh token will be used to automatically get new access tokens when they expire.")
    else:
        print("Error: No access token in response")
        print(f"Response: {result}")
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
    if hasattr(e, 'response') and e.response:
        print(f"Response: {e.response.text}")

