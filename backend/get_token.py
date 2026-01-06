#!/usr/bin/env python3
"""
Helper script to get a Strava access token with the correct scope.
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_access_token():
    """Exchange authorization code for access token."""
    client_id = os.getenv('STRAVA_CLIENT_ID')
    client_secret = os.getenv('STRAVA_CLIENT_SECRET')
    code = input("Enter the authorization code from the redirect URL: ").strip()
    
    if not client_id or not client_secret:
        print("Error: STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be in .env file")
        print("\nAdd these to your .env file:")
        print("STRAVA_CLIENT_ID=your_client_id")
        print("STRAVA_CLIENT_SECRET=your_client_secret")
        return None
    
    url = "https://www.strava.com/oauth/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code"
    }
    
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        result = response.json()
        
        access_token = result.get('access_token')
        if access_token:
            print(f"\n✅ Success! Your access token is:")
            print(f"{access_token}")
            print(f"\nAdd this to your .env file:")
            print(f"STRAVA_ACCESS_TOKEN={access_token}")
            return access_token
        else:
            print("Error: No access token in response")
            print(f"Response: {result}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return None


def main():
    print("=" * 60)
    print("Strava Access Token Helper")
    print("=" * 60)
    print("\n1. Go to https://www.strava.com/settings/api")
    print("2. Find your Client ID")
    print("3. Visit this URL (replace YOUR_CLIENT_ID with your Client ID):")
    print("\n   https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&scope=activity:read_all")
    print("\n4. After authorizing, you'll be redirected to a URL like:")
    print("   http://localhost/?code=abc123&scope=read,activity:read_all")
    print("\n5. Copy the 'code' value from that URL")
    print("\n" + "=" * 60)
    
    get_access_token()


if __name__ == "__main__":
    main()

