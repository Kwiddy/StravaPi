#!/usr/bin/env python3
"""
Flask API server for Strava Dashboard.
Serves runs and swims data to the frontend.
"""

from flask import Flask, jsonify, request
from strava_runs import get_access_token, get_activities as fetch_strava_activities, format_duration, format_distance
from datetime import datetime

app = Flask(__name__)

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


@app.route('/api/runs', methods=['GET'])
def get_runs_and_swims():
    """Get all runs and swims from the start of the current year."""
    try:
        # Get access token
        access_token = get_access_token()
        if not access_token:
            return jsonify({'error': 'Failed to get access token. Please check your .env file.'}), 500
        
        # Fetch activities - get more to ensure we have enough for the year
        activities = fetch_strava_activities(access_token, per_page=200)
        if activities is None:
            return jsonify({'error': 'Failed to fetch activities from Strava.'}), 500
        
        if not isinstance(activities, list):
            return jsonify({'error': 'Invalid response from Strava API.'}), 500
        
        # Filter for runs and swims
        runs_and_swims = filter_runs_and_swims(activities)
        
        # Filter by current year
        current_year_activities = filter_by_current_year(runs_and_swims)
        
        # Sort by date (newest first) - use a safe key function
        def get_sort_date(activity):
            date_str = activity.get('start_date_local', '') or activity.get('start_date', '') or '0000-01-01'
            return date_str
        
        current_year_activities.sort(key=get_sort_date, reverse=True)
        
        if not current_year_activities:
            return jsonify({'activities': []}), 200
        
        # Format activities for JSON response
        formatted_activities = []
        for activity in current_year_activities:
            try:
                formatted = format_activity_data(activity)
                formatted_activities.append(formatted)
            except Exception as e:
                print(f"Error formatting activity {activity.get('id', 'unknown')}: {e}")
                continue
        
        return jsonify({'activities': formatted_activities}), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in get_activities: {e}")
        print(f"Traceback: {error_trace}")
        return jsonify({'error': str(e), 'details': error_trace}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    print("Starting Strava Dashboard API server on http://localhost:5489")
    print("CORS enabled for all origins")
    app.run(debug=True, port=5489, host='0.0.0.0')
