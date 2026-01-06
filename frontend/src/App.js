import React, { useState, useEffect } from 'react';
import './App.css';

const API_URL = 'http://localhost:5489/api/runs';

function App() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchRuns();
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchRuns, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchRuns = async () => {
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
        setRuns(data.runs || []);
      }
    } catch (err) {
      console.error('Error fetching runs:', err);
      setError(`Failed to connect to backend: ${err.message}. Make sure the API server is running on port 5489.`);
    } finally {
      setLoading(false);
    }
  };

  const formatPace = (paceMin, paceSec) => {
    if (paceMin === null || paceSec === null) return 'N/A';
    return `${paceMin}:${paceSec.toString().padStart(2, '0')} min/km`;
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Strava Dashboard</h1>
        <p>Your Latest 3 Runs</p>
        <button onClick={fetchRuns} className="refresh-btn" disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </header>
      
      <main className="App-main">
        {loading && runs.length === 0 && (
          <div className="loading">Loading runs...</div>
        )}
        
        {error && (
          <div className="error">
            <p>{error}</p>
            <button onClick={fetchRuns}>Retry</button>
          </div>
        )}
        
        {!loading && !error && runs.length === 0 && (
          <div className="no-runs">No runs found.</div>
        )}
        
        {!loading && !error && runs.length > 0 && (
          <div className="runs-container">
            {runs.map((run, index) => (
              <div key={index} className="run-card">
                <h2>{run.name}</h2>
                <div className="run-details">
                  <div className="detail-row">
                    <span className="label">Date:</span>
                    <span className="value">{run.date}</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Distance:</span>
                    <span className="value">{run.distance_km} km</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Duration:</span>
                    <span className="value">{run.duration}</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Pace:</span>
                    <span className="value">{formatPace(run.pace_min, run.pace_sec)}</span>
                  </div>
                  {run.elevation_gain_m > 0 && (
                    <div className="detail-row">
                      <span className="label">Elevation Gain:</span>
                      <span className="value">{run.elevation_gain_m} m</span>
                    </div>
                  )}
                  {run.average_heartrate && (
                    <div className="detail-row">
                      <span className="label">Avg Heart Rate:</span>
                      <span className="value">{run.average_heartrate} bpm</span>
                    </div>
                  )}
                  {run.description && (
                    <div className="detail-row description">
                      <span className="label">Description:</span>
                      <span className="value">{run.description}</span>
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
