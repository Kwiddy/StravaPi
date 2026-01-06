import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchRuns();
  }, []);

  const fetchRuns = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:5000/api/runs');
      const data = await response.json();
      
      if (response.ok) {
        setRuns(data.runs || []);
        setError(null);
      } else {
        setError(data.error || 'Failed to fetch runs');
      }
    } catch (err) {
      setError('Failed to connect to backend. Make sure the API server is running on port 5000.');
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
        <p>Your Latest Runs</p>
      </header>
      
      <main className="App-main">
        {loading && <div className="loading">Loading runs...</div>}
        
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

