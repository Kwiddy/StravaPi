#!/usr/bin/env python3
"""
Temporary script to reset the activities cache and re-fetch ALL activities from the start of the year.
Use this when the first week's activities (late Dec of previous year) were missed.

Run from the project root: python backend/reset_cache.py
Or from backend: python reset_cache.py
"""

import os
import sys
from datetime import datetime, timedelta

# Ensure backend directory is in path and we load .env from there
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from dotenv import load_dotenv
load_dotenv()

import requests

from strava_runs import get_access_token
from api import (
    filter_runs_and_swims,
    filter_by_current_year,
    format_activity_data,
    ACTIVITIES_FILE,
    save_activities,
)


def get_year_start_timestamp():
    """Unix timestamp for the Monday of the week containing Jan 1."""
    year_start = datetime(datetime.now().year, 1, 1)
    first_monday = year_start - timedelta(days=year_start.weekday())
    return int(first_monday.timestamp())


def fetch_activities(access_token, per_page=200, after=None, page=1):
    """Fetch activities from Strava API with optional after (Unix timestamp) and page."""
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"per_page": per_page, "page": page}
    if after is not None:
        params["after"] = int(after)
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    return None


def main():
    print("Resetting activities cache...")

    access_token = get_access_token()
    if not access_token:
        print("Error: Could not get access token. Check your .env file.")
        sys.exit(1)

    # Remove existing cache
    if os.path.exists(ACTIVITIES_FILE):
        os.remove(ACTIVITIES_FILE)
        print(f"Removed {ACTIVITIES_FILE}")
    else:
        print("No existing cache file found.")

    # Fetch from year start
    year_start_ts = get_year_start_timestamp()
    year_start_date = datetime.fromtimestamp(year_start_ts).strftime("%Y-%m-%d")
    print(f"Fetching all activities from {year_start_date} onward...")

    per_page = 200  # Strava max per page
    page = 1
    all_activities = {}
    total_fetched = 0

    while True:
        activities = fetch_activities(
            access_token,
            per_page=per_page,
            after=year_start_ts,
            page=page,
        )

        if not activities or not isinstance(activities, list):
            break

        runs_and_swims = filter_runs_and_swims(activities)
        current_year = filter_by_current_year(runs_and_swims)

        for activity in current_year:
            activity_id = str(activity.get("id", ""))
            if not activity_id or activity_id in all_activities:
                continue
            try:
                formatted = format_activity_data(activity)
                all_activities[activity_id] = formatted
                total_fetched += 1
            except Exception as e:
                print(f"  Warning: Could not format activity {activity_id}: {e}")

        if len(activities) < per_page:
            break

        page += 1
        print(f"  Fetched page {page - 1} ({len(activities)} activities)...")

    cache_data = {
        "metadata": {
            "last_sync": datetime.now().isoformat(),
            "last_activity_timestamp": None,
            "total_activities": len(all_activities),
        },
        "activities": all_activities,
    }

    if all_activities:
        dates = [a.get("date", "") for a in all_activities.values() if a.get("date")]
        if dates:
            dates.sort(reverse=True)
            cache_data["metadata"]["last_activity_timestamp"] = dates[0]

    if save_activities(cache_data):
        print(f"Done. Cached {len(all_activities)} activities.")
    else:
        print("Error: Failed to save cache.")
        sys.exit(1)


if __name__ == "__main__":
    main()
