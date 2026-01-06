#!/usr/bin/env python3
"""
Flask API server for Strava Dashboard.
Serves the latest runs data to the frontend.
"""

from flask import Flask, jsonify
from strava_runs import get_access_token, get_activities, filter_runs, format_duration, format_distance
from datetime import datetime

app = Flask(__name__)

# Try to use flask-cors if available, otherwise use manual headers
try:
    from flask_cors import CORS
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
except ImportError:
    # Fallback: Add CORS headers manually
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response


def format_run_data(run):
    """Format run data for JSON response."""
    distance = run.get('distance', 0)
    moving_time = run.get('moving_time', 0)
    
    # Calculate pace
    pace_min = None
    pace_sec = None
    if distance > 0 and moving_time > 0:
        pace_seconds_per_km = moving_time / (distance / 1000)
        pace_min = int(pace_seconds_per_km // 60)
        pace_sec = int(pace_seconds_per_km % 60)
    
    # Format date
    start_date = run.get('start_date_local', '')
    formatted_date = None
    if start_date:
        try:
            date_obj = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
        except:
            formatted_date = start_date
    
    return {
        'name': run.get('name', 'Untitled Run'),
        'date': formatted_date,
        'distance_km': round(format_distance(distance), 2),
        'duration': format_duration(moving_time),
        'pace_min': pace_min,
        'pace_sec': pace_sec,
        'elevation_gain_m': round(run.get('total_elevation_gain', 0)),
        'average_heartrate': round(run.get('average_heartrate', 0)) if run.get('average_heartrate') else None,
        'description': run.get('description', '')
    }


@app.route('/api/runs', methods=['GET'])
def get_runs():
    """Get the latest 3 runs from Strava."""
    try:
        # Get access token
        access_token = get_access_token()
        if not access_token:
            return jsonify({'error': 'Failed to get access token. Please check your .env file.'}), 500
        
        # Fetch activities
        activities = get_activities(access_token)
        if activities is None:
            return jsonify({'error': 'Failed to fetch activities from Strava.'}), 500
        
        # Filter for runs
        runs = filter_runs(activities)
        
        if not runs:
            return jsonify({'runs': []}), 200
        
        # Get latest 3 runs
        latest_runs = runs[:3]
        
        # Format runs for JSON response
        formatted_runs = [format_run_data(run) for run in latest_runs]
        
        return jsonify({'runs': formatted_runs}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)

