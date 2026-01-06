#!/usr/bin/env python3
"""
Flask API server for Strava Dashboard.
Serves runs and swims data to the frontend with local caching.
"""

import os
import json
import tempfile
import shutil
from flask import Flask, jsonify, request
from strava_runs import get_access_token, get_activities as fetch_strava_activities, format_duration, format_distance
from datetime import datetime

app = Flask(__name__)

# Path to activities cache file
ACTIVITIES_FILE = os.path.join(os.path.dirname(__file__), 'activities.json')

# Simple CORS handler - ONE place only
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

# Handle OPTIONS preflight
@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response


def load_activities():
    """Load activities from local JSON file."""
    if not os.path.exists(ACTIVITIES_FILE):
        return {
            'metadata': {
                'last_sync': None,
                'last_activity_timestamp': None,
                'total_activities': 0
            },
            'activities': {}
        }
    
    try:
        with open(ACTIVITIES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure structure is correct
            if 'activities' not in data:
                data['activities'] = {}
            if 'metadata' not in data:
                data['metadata'] = {
                    'last_sync': None,
                    'last_activity_timestamp': None,
                    'total_activities': len(data.get('activities', {}))
                }
            return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading activities file: {e}")
        # Return empty structure if file is corrupted
        return {
            'metadata': {
                'last_sync': None,
                'last_activity_timestamp': None,
                'total_activities': 0
            },
            'activities': {}
        }


def save_activities(data):
    """Save activities to local JSON file (atomic write)."""
    try:
        # Write to temporary file first
        temp_file = ACTIVITIES_FILE + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Atomically replace the original file
        shutil.move(temp_file, ACTIVITIES_FILE)
        return True
    except Exception as e:
        print(f"Error saving activities file: {e}")
        # Clean up temp file if it exists
        if os.path.exists(ACTIVITIES_FILE + '.tmp'):
            try:
                os.remove(ACTIVITIES_FILE + '.tmp')
            except:
                pass
        return False


def filter_runs_and_swims(activities):
    """Filter activities to only include runs and swims."""
    return [activity for activity in activities if activity.get('type') in ['Run', 'Swim']]


def filter_by_current_year(activities):
    """Filter activities to only include those from the start of the current year."""
    current_year = datetime.now().year
    year_start_str = f"{current_year}-01-01"
    
    filtered = []
    for activity in activities:
        start_date = activity.get('start_date_local', '') or activity.get('start_date', '')
        if start_date:
            # Simple string comparison - Strava dates are ISO format
            # Compare just the date part (first 10 characters: YYYY-MM-DD)
            if start_date[:10] >= year_start_str:
                filtered.append(activity)
    
    return filtered


def format_activity_data(activity):
    """Format activity data (run or swim) for JSON response."""
    if not activity:
        raise ValueError("Activity is None or empty")
    
    activity_type = activity.get('type', 'Unknown')
    distance = activity.get('distance', 0) or 0
    moving_time = activity.get('moving_time', 0) or 0
    
    # Calculate pace (for runs) or pace per 100m (for swims)
    pace_min = None
    pace_sec = None
    if distance > 0 and moving_time > 0:
        if activity_type == 'Run':
            # Pace per km for runs
            pace_seconds_per_km = moving_time / (distance / 1000)
            pace_min = int(pace_seconds_per_km // 60)
            pace_sec = int(pace_seconds_per_km % 60)
        elif activity_type == 'Swim':
            # Pace per 100m for swims
            pace_seconds_per_100m = moving_time / (distance / 100)
            pace_min = int(pace_seconds_per_100m // 60)
            pace_sec = int(pace_seconds_per_100m % 60)
    
    # Format date - simple approach, just clean up the ISO format
    start_date = activity.get('start_date_local', '') or activity.get('start_date', '')
    formatted_date = start_date
    if start_date:
        try:
            # Remove timezone info and format nicely
            date_str = start_date.replace('Z', '').split('+')[0].split('.')[0]
            # Convert to datetime and format
            date_obj = datetime.fromisoformat(date_str)
            formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
        except:
            # If parsing fails, just use the original string
            formatted_date = start_date
    
    # Format distance - km for runs, meters for swims
    if activity_type == 'Swim':
        distance_display = f"{round(distance, 0)} m"
    else:
        distance_display = f"{round(format_distance(distance), 2)} km"
    
    return {
        'id': str(activity.get('id', '')),
        'type': activity_type,
        'name': activity.get('name', f'Untitled {activity_type}'),
        'date': formatted_date,
        'distance': distance_display,
        'distance_meters': round(distance, 0),
        'duration': format_duration(moving_time),
        'pace_min': pace_min,
        'pace_sec': pace_sec,
        'elevation_gain_m': round(activity.get('total_elevation_gain', 0)),
        'average_heartrate': round(activity.get('average_heartrate', 0)) if activity.get('average_heartrate') else None,
        'description': activity.get('description', '')
    }


def get_cached_activities():
    """Get formatted activities from cache."""
    cache_data = load_activities()
    activities_dict = cache_data.get('activities', {})
    
    # Filter by current year
    current_year = datetime.now().year
    year_start_str = f"{current_year}-01-01"
    
    current_year_activities = []
    for activity_id, activity in activities_dict.items():
        start_date = activity.get('date', '')
        if start_date and start_date[:10] >= year_start_str:
            current_year_activities.append(activity)
    
    # Sort by date (newest first)
    current_year_activities.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    return current_year_activities


def merge_new_activities(new_activities, existing_activities):
    """Merge new activities into existing ones, avoiding duplicates."""
    new_count = 0
    existing_ids = set(existing_activities.keys())
    
    for activity in new_activities:
        activity_id = str(activity.get('id', ''))
        if activity_id and activity_id not in existing_ids:
            # Format and add new activity
            try:
                formatted = format_activity_data(activity)
                existing_activities[activity_id] = formatted
                new_count += 1
            except Exception as e:
                print(f"Error formatting activity {activity_id}: {e}")
                continue
    
    return new_count


@app.route('/api/runs', methods=['GET'])
def get_runs_and_swims():
    """Get all runs and swims from cache (fast, no API call)."""
    try:
        activities = get_cached_activities()
        return jsonify({
            'activities': activities,
            'cached': True,
            'count': len(activities)
        }), 200
    except Exception as e:
        print(f"Error getting cached activities: {e}")
        return jsonify({'error': str(e), 'activities': []}), 500


@app.route('/api/runs/refresh', methods=['POST'])
def refresh_activities():
    """Fetch new activities from Strava API and update cache."""
    try:
        # Get access token
        access_token = get_access_token()
        if not access_token:
            return jsonify({'error': 'Failed to get access token. Please check your .env file.'}), 500
        
        # Load existing activities
        cache_data = load_activities()
        existing_activities = cache_data.get('activities', {})
        existing_ids = set(existing_activities.keys())
        
        # Fetch activities in small batches, stopping when we find duplicates
        per_page = 20
        page = 1
        new_count = 0
        found_duplicate = False
        
        while not found_duplicate and page <= 10:  # Limit to 10 pages (200 activities max)
            activities = fetch_strava_activities(access_token, per_page=per_page)
            if activities is None:
                break
            
            if not isinstance(activities, list) or len(activities) == 0:
                break
            
            # Filter for runs and swims
            runs_and_swims = filter_runs_and_swims(activities)
            
            # Filter by current year
            current_year_activities = filter_by_current_year(runs_and_swims)
            
            # Check each activity - stop if we find one we already have
            for activity in current_year_activities:
                activity_id = str(activity.get('id', ''))
                if activity_id in existing_ids:
                    found_duplicate = True
                    break
                
                # Add new activity
                try:
                    formatted = format_activity_data(activity)
                    existing_activities[activity_id] = formatted
                    new_count += 1
                except Exception as e:
                    print(f"Error formatting activity {activity_id}: {e}")
                    continue
            
            # If we got fewer activities than requested, we've reached the end
            if len(activities) < per_page:
                break
            
            page += 1
        
        # Update metadata
        cache_data['activities'] = existing_activities
        cache_data['metadata'] = {
            'last_sync': datetime.now().isoformat(),
            'last_activity_timestamp': None,
            'total_activities': len(existing_activities)
        }
        
        # Find most recent activity timestamp
        if existing_activities:
            dates = [a.get('date', '') for a in existing_activities.values() if a.get('date')]
            if dates:
                dates.sort(reverse=True)
                cache_data['metadata']['last_activity_timestamp'] = dates[0]
        
        # Save to file
        if save_activities(cache_data):
            return jsonify({
                'success': True,
                'new_activities': new_count,
                'total_activities': len(existing_activities),
                'last_sync': cache_data['metadata']['last_sync']
            }), 200
        else:
            return jsonify({'error': 'Failed to save activities to cache'}), 500
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in refresh_activities: {e}")
        print(f"Traceback: {error_trace}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    print("Starting Strava Dashboard API server on http://localhost:5489")
    print("CORS enabled for all origins")
    print(f"Activities cache: {ACTIVITIES_FILE}")
    app.run(debug=True, port=5489, host='0.0.0.0')
