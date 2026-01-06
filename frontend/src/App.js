import React, { useState, useEffect } from 'react';
import './App.css';

const API_URL = 'http://localhost:5489/api/runs';

function App() {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchActivities();
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchActivities, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchActivities = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(API_URL, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.error) {
        setError(data.error);
      } else {
        setActivities(data.activities || []);
      }
    } catch (err) {
      console.error('Error fetching activities:', err);
      setError(`Failed to connect to backend: ${err.message}. Make sure the API server is running on port 5489.`);
    } finally {
      setLoading(false);
    }
  };

  const formatPace = (paceMin, paceSec, activityType) => {
    if (paceMin === null || paceSec === null) return 'N/A';
    const paceStr = `${paceMin}:${paceSec.toString().padStart(2, '0')}`;
    if (activityType === 'Swim') {
      return `${paceStr} min/100m`;
    }
    return `${paceStr} min/km`;
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <div className="logo-section">
            <svg className="logo-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <div className="logo-text">
              <h1>Strava Dashboard</h1>
              <p>Runs & Swims - {new Date().getFullYear()}</p>
            </div>
          </div>
          <button onClick={fetchActivities} className="refresh-btn" disabled={loading} title="Refresh">
            <svg className="refresh-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M1 4V10H7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M23 20V14H17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10M23 14L18.36 18.36A9 9 0 0 1 3.51 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </header>
      
      <main className="App-main">
        {loading && activities.length === 0 && (
          <div className="loading">Loading activities...</div>
        )}
        
        {error && (
          <div className="error">
            <p>{error}</p>
            <button onClick={fetchActivities}>Retry</button>
          </div>
        )}
        
        {!loading && !error && activities.length === 0 && (
          <div className="no-runs">No runs or swims found for {new Date().getFullYear()}.</div>
        )}
        
        {!loading && !error && activities.length > 0 && (
          <div className="runs-container">
            {activities.map((activity, index) => (
              <div key={index} className={`run-card ${activity.type.toLowerCase()}-card`}>
                <div className="activity-header">
                  <h2>{activity.name}</h2>
                  <span className={`activity-type ${activity.type.toLowerCase()}-badge`}>
                    {activity.type}
                  </span>
                </div>
                <div className="run-details">
                  <div className="detail-row">
                    <span className="label">Date:</span>
                    <span className="value">{activity.date}</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Distance:</span>
                    <span className="value">{activity.distance}</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Duration:</span>
                    <span className="value">{activity.duration}</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Pace:</span>
                    <span className="value">{formatPace(activity.pace_min, activity.pace_sec, activity.type)}</span>
                  </div>
                  {activity.elevation_gain_m > 0 && (
                    <div className="detail-row">
                      <span className="label">Elevation Gain:</span>
                      <span className="value">{activity.elevation_gain_m} m</span>
                    </div>
                  )}
                  {activity.average_heartrate && (
                    <div className="detail-row">
                      <span className="label">Avg Heart Rate:</span>
                      <span className="value">{activity.average_heartrate} bpm</span>
                    </div>
                  )}
                  {activity.description && (
                    <div className="detail-row description">
                      <span className="label">Description:</span>
                      <span className="value">{activity.description}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
