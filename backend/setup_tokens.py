#!/usr/bin/env python3
"""
Interactive script to set up all Strava tokens in .env file.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def update_env_file(key, value):
    """Update or add a key-value pair in .env file."""
    env_path = '.env'
    
    # Read existing .env file
    lines = []
    key_found = False
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
    
    # Update or add the key
    with open(env_path, 'w') as f:
        for line in lines:
            if line.startswith(f'{key}='):
                f.write(f'{key}={value}\n')
                key_found = True
            else:
                f.write(line)
        
        if not key_found:
            f.write(f'{key}={value}\n')

def get_new_tokens():
    """Get new tokens using authorization code."""
    print("\n" + "="*60)
    print("Getting New Tokens")
    print("="*60)
    
    # Try to get from .env first
    client_id = os.getenv('STRAVA_CLIENT_ID')
    client_secret = os.getenv('STRAVA_CLIENT_SECRET')
    
    if not client_id:
        client_id = input("\nEnter your Strava Client ID: ").strip()
    else:
        print(f"\nUsing Client ID from .env: {client_id}")
    
    if not client_secret:
        client_secret = input("Enter your Strava Client Secret: ").strip()
    else:
        print(f"Using Client Secret from .env: {'*' * len(client_secret)}")
    
    print("\nVisit this URL in your browser:")
    print(f"https://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri=http://localhost&scope=activity:read_all")
    print("\nAfter authorizing, you'll be redirected to a URL like:")
    print("http://localhost/?code=abc123&scope=read,activity:read_all")
    
    code = input("\nEnter the code from the redirect URL: ").strip()
    
    url = "https://www.strava.com/oauth/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code"
    }
    
    try:
        print("\nExchanging code for tokens...")
        response = requests.post(url, data=data)
        response.raise_for_status()
        result = response.json()
        
        access_token = result.get('access_token')
        refresh_token = result.get('refresh_token')
        
        if access_token:
            # Update .env file
            update_env_file('STRAVA_CLIENT_ID', client_id)
            update_env_file('STRAVA_CLIENT_SECRET', client_secret)
            update_env_file('STRAVA_ACCESS_TOKEN', access_token)
            if refresh_token:
                update_env_file('STRAVA_REFRESH_TOKEN', refresh_token)
            
            print("\n✅ Success! All tokens have been saved to .env file:")
            print(f"   - Client ID: {client_id}")
            print(f"   - Client Secret: {'*' * len(client_secret)}")
            print(f"   - Access Token: {access_token[:20]}...")
            if refresh_token:
                print(f"   - Refresh Token: {refresh_token[:20]}...")
            print("\nYour tokens are now set up for automatic refresh!")
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

def main():
    print("="*60)
    print("Strava Token Setup")
    print("="*60)
    
    current_token = os.getenv('STRAVA_ACCESS_TOKEN')
    current_refresh = os.getenv('STRAVA_REFRESH_TOKEN')
    current_client_id = os.getenv('STRAVA_CLIENT_ID')
    current_client_secret = os.getenv('STRAVA_CLIENT_SECRET')
    
    print("\nCurrent .env status:")
    print(f"  Access Token: {'✓ Set' if current_token else '✗ Missing'}")
    print(f"  Refresh Token: {'✓ Set' if current_refresh else '✗ Missing'}")
    print(f"  Client ID: {'✓ Set' if current_client_id else '✗ Missing'}")
    print(f"  Client Secret: {'✓ Set' if current_client_secret else '✗ Missing'}")
    
    if current_refresh and current_client_id and current_client_secret:
        print("\n✅ You already have all tokens set up!")
        print("You can refresh your access token by running: python refresh_token.py")
        response = input("\nDo you want to get new tokens anyway? (y/n): ").strip().lower()
        if response != 'y':
            return
    
    print("\nTo get your Client ID and Client Secret:")
    print("1. Go to https://www.strava.com/settings/api")
    print("2. Find your application or create a new one")
    
    get_new_tokens()

if __name__ == "__main__":
    main()

