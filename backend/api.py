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
from datetime import datetime, timedelta

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
    formatted_date_display = start_date  # For display in tables
    if start_date:
        try:
            # Remove timezone info and format nicely
            date_str = start_date.replace('Z', '').split('+')[0].split('.')[0]
            # Convert to datetime and format
            date_obj = datetime.fromisoformat(date_str)
            formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
            # Format for display: "DD-MM-YYYY HH:MM"
            formatted_date_display = date_obj.strftime('%d-%m-%Y %H:%M')
        except:
            # If parsing fails, just use the original string
            formatted_date = start_date
            formatted_date_display = start_date
    
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
        'date_display': formatted_date_display,
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


def calculate_statistics():
    """Calculate statistics from cached activities."""
    activities = get_cached_activities()
    
    runs = [a for a in activities if a.get('type') == 'Run']
    swims = [a for a in activities if a.get('type') == 'Swim']
    
    # Total distances
    total_run_distance = sum(a.get('distance_meters', 0) for a in runs)
    total_swim_distance = sum(a.get('distance_meters', 0) for a in swims)
    
    # Calculate weeks in current year
    now = datetime.now()
    year_start = datetime(now.year, 1, 1)
    days_elapsed = (now - year_start).days
    weeks_elapsed = max(days_elapsed / 7, 1)  # At least 1 week (for schedule calculations)
    
    # Calculate the first Monday of the year (or the Monday of the week containing Jan 1)
    year_start_weekday = year_start.weekday()  # 0 = Monday, 6 = Sunday
    first_monday = year_start - timedelta(days=year_start_weekday)
    
    # Calculate weekly breakdown for line charts using Monday-based weeks
    def get_week_number(date_str):
        """Get week number from date string using Monday-based weeks."""
        try:
            # Parse the date string (format: "2026-01-06 12:30:00" or "2026-01-06")
            date_obj = datetime.strptime(date_str[:10], '%Y-%m-%d')
            # Calculate days since first Monday
            days_since_first_monday = (date_obj - first_monday).days
            week_num = days_since_first_monday // 7  # Integer division gives week number
            return max(0, week_num)
        except Exception as e:
            print(f"Error parsing date '{date_str}': {e}")
            return 0
    
    def get_monday_of_week(week_num):
        """Get the Monday date for a given week number."""
        monday = first_monday + timedelta(weeks=week_num)
        return monday.strftime('%d %b')  # e.g., "06 Jan"
    
    # Calculate current week number using the same logic
    current_week = get_week_number(now.strftime('%Y-%m-%d'))
    
    # Group activities by week
    weekly_runs = {}
    weekly_swims = {}
    
    for run in runs:
        week = get_week_number(run.get('date', ''))
        if week not in weekly_runs:
            weekly_runs[week] = 0
        weekly_runs[week] += run.get('distance_meters', 0) / 1000  # Convert to km
    
    for swim in swims:
        week = get_week_number(swim.get('date', ''))
        if week not in weekly_swims:
            weekly_swims[week] = 0
        weekly_swims[week] += swim.get('distance_meters', 0)  # Keep in meters
    
    # Calculate average weekly distances based on actual number of weeks (current_week + 1)
    # This includes the current week (0-indexed, so week 0, 1, 2 = 3 weeks)
    num_weeks = current_week + 1
    avg_weekly_run = (total_run_distance / 1000) / num_weeks if num_weeks > 0 else 0
    avg_weekly_swim = total_swim_distance / num_weeks if num_weeks > 0 else 0
    
    # Create weekly data arrays (last 12 weeks or all weeks if less, including current week)
    weeks_to_show = min(12, num_weeks)  # Number of weeks to display
    start_week = max(0, current_week - weeks_to_show + 1)  # Start from this week number
    
    weekly_run_data = []
    weekly_swim_data = []
    
    # Include all weeks from start_week to current_week (inclusive)
    for week in range(start_week, current_week + 1):
        # Get Monday date for this week
        week_label = get_monday_of_week(week)
        weekly_run_data.append({
            'week': week_label,
            'distance': round(weekly_runs.get(week, 0), 2)
        })
        weekly_swim_data.append({
            'week': week_label,
            'distance': round(weekly_swims.get(week, 0), 0)
        })
    
    # Number of swims and percentage (84 swims = 100%)
    num_swims = len(swims)
    swim_percentage = min((num_swims / 84) * 100, 100) if 84 > 0 else 0
    
    # Calculate if ahead or behind schedule
    # Target: 84 swims over 52 weeks = ~1.615 swims per week
    target_swims_by_now = (weeks_elapsed / 52) * 84
    swims_ahead = num_swims - target_swims_by_now
    is_ahead = swims_ahead >= 0
    schedule_status = 'ahead' if is_ahead else 'behind'
    
    # Running distance percentage (1500km = 100%)
    run_distance_km = total_run_distance / 1000
    run_distance_percentage = min((run_distance_km / 1500) * 100, 100) if 1500 > 0 else 0
    
    # Calculate if ahead or behind schedule for running distance (1500km over 52 weeks)
    target_distance_by_now = (weeks_elapsed / 52) * 1500
    distance_ahead = run_distance_km - target_distance_by_now
    is_ahead_distance = distance_ahead >= 0
    distance_schedule_status = 'ahead' if is_ahead_distance else 'behind'
    
    # Marathon statistics
    half_marathons = len([r for r in runs if 21.1 <= (r.get('distance_meters', 0) / 1000) < 42.2])
    full_marathons = len([r for r in runs if 42.2 <= (r.get('distance_meters', 0) / 1000) < 50.0])
    ultra_marathons = len([r for r in runs if (r.get('distance_meters', 0) / 1000) >= 50.0])
    
    return {
        'total_run_distance_km': round(total_run_distance / 1000, 2),
        'total_swim_distance_m': round(total_swim_distance, 0),
        'avg_weekly_run_distance_km': round(avg_weekly_run, 2),
        'avg_weekly_swim_distance_m': round(avg_weekly_swim, 0),
        'num_swims': num_swims,
        'swim_percentage': round(swim_percentage, 1),
        'num_runs': len(runs),
        'weeks_elapsed': round(weeks_elapsed, 1),
        'weekly_run_data': weekly_run_data,
        'weekly_swim_data': weekly_swim_data,
        'swims_ahead': round(swims_ahead, 1),
        'schedule_status': schedule_status,
        'target_swims_by_now': round(target_swims_by_now, 1),
        'run_distance_percentage': round(run_distance_percentage, 1),
        'distance_ahead': round(distance_ahead, 1),
        'distance_schedule_status': distance_schedule_status,
        'half_marathons': half_marathons,
        'full_marathons': full_marathons,
        'ultra_marathons': ultra_marathons
    }


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get statistics about runs and swims."""
    try:
        stats = calculate_statistics()
        return jsonify(stats), 200
    except Exception as e:
        print(f"Error calculating statistics: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/activities/<activity_type>', methods=['GET'])
def get_activities_by_type(activity_type):
    """Get all activities of a specific type (Run or Swim) for table view."""
    try:
        activities = get_cached_activities()
        filtered = [a for a in activities if a.get('type', '').lower() == activity_type.lower()]
        
        # Sort by date (newest first)
        filtered.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return jsonify({
            'activities': filtered,
            'type': activity_type,
            'count': len(filtered)
        }), 200
    except Exception as e:
        print(f"Error getting activities by type: {e}")
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
