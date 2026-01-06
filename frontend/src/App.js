import React, { useState, useEffect } from 'react';
import { LineChart, Line, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts';
import './App.css';

const API_URL = 'http://localhost:5489/api/runs';
const REFRESH_URL = 'http://localhost:5489/api/runs/refresh';
const STATS_URL = 'http://localhost:5489/api/statistics';
const ACTIVITIES_BY_TYPE_URL = 'http://localhost:5489/api/activities';

function App() {
  const [activities, setActivities] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [selectedActivityType, setSelectedActivityType] = useState(null);
  const [detailActivities, setDetailActivities] = useState([]);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    loadCachedActivities();
    loadStatistics();
  }, []);

  const loadCachedActivities = async () => {
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
      console.error('Error loading cached activities:', err);
      setError(`Failed to connect to backend: ${err.message}. Make sure the API server is running on port 5489.`);
    } finally {
      setLoading(false);
    }
  };

  const loadStatistics = async () => {
    try {
      const response = await fetch(STATS_URL);
      if (response.ok) {
        const data = await response.json();
        setStatistics(data);
      }
    } catch (err) {
      console.error('Error loading statistics:', err);
    }
  };

  const refreshActivities = async () => {
    try {
      setRefreshing(true);
      setError(null);
      
      const response = await fetch(REFRESH_URL, {
        method: 'POST',
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
        await loadCachedActivities();
        await loadStatistics();
        if (data.new_activities > 0) {
          console.log(`Added ${data.new_activities} new activities`);
        }
      }
    } catch (err) {
      console.error('Error refreshing activities:', err);
      setError(`Failed to refresh activities: ${err.message}`);
    } finally {
      setRefreshing(false);
    }
  };

  const handleActivityClick = async (activityType) => {
    try {
      const response = await fetch(`${ACTIVITIES_BY_TYPE_URL}/${activityType}`);
      if (response.ok) {
        const data = await response.json();
        setDetailActivities(data.activities || []);
        setSelectedActivityType(activityType);
        setShowModal(true);
      }
    } catch (err) {
      console.error('Error loading detail activities:', err);
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

  // Prepare chart data for weekly averages
  const weeklyChartData = statistics ? [
    { name: 'Runs', value: statistics.avg_weekly_run_distance_km, color: '#fc5200' },
    { name: 'Swims', value: statistics.avg_weekly_swim_distance_m / 1000, color: '#00a8cc' }
  ] : [];

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
          <button onClick={refreshActivities} className="refresh-btn" disabled={refreshing || loading} title="Refresh from Strava">
            <svg className={`refresh-icon ${refreshing ? 'spinning' : ''}`} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
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
            <button onClick={loadCachedActivities}>Retry</button>
          </div>
        )}

        {!loading && !error && statistics && (
          <div className="dashboard-split">
            <div className="dashboard-column runs-column">
              <h2 className="column-title">Running</h2>
              <div className="statistics-grid">
                <div className="stat-tile" onClick={() => handleActivityClick('Run')}>
                  <h3>Running Statistics</h3>
                  <div className="stat-values-row">
                    <div className="stat-value-item">
                      <div className="stat-label-small">Total Distance</div>
                      <div className="stat-value">{statistics.total_run_distance_km.toLocaleString()} km</div>
                    </div>
                    <div className="stat-value-item">
                      <div className="stat-label-small">Avg Weekly</div>
                      <div className="stat-value">{statistics.avg_weekly_run_distance_km.toFixed(1)} km</div>
                    </div>
                  </div>
                  <ResponsiveContainer width="100%" height={180}>
                    <LineChart data={statistics.weekly_run_data || []}>
                      <XAxis dataKey="week" stroke="#888" fontSize={12} />
                      <YAxis stroke="#888" fontSize={12} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#2a2a2a', border: '1px solid #3a3a3a', borderRadius: '8px' }}
                        labelStyle={{ color: '#e0e0e0' }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="distance" 
                        stroke="#fc5200" 
                        strokeWidth={3} 
                        dot={{ fill: '#fc5200', r: 4 }} 
                        activeDot={{ r: 6 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            <div className="dashboard-column swims-column">
              <h2 className="column-title">Swimming</h2>
              <div className="statistics-grid">
                <div className="stat-tile" onClick={() => handleActivityClick('Swim')}>
                  <h3>Swimming Statistics</h3>
                  <div className="stat-values-row">
                    <div className="stat-value-item">
                      <div className="stat-label-small">Total Distance</div>
                      <div className="stat-value">{statistics.total_swim_distance_m.toLocaleString()} m</div>
                    </div>
                    <div className="stat-value-item">
                      <div className="stat-label-small">Avg Weekly</div>
                      <div className="stat-value">{statistics.avg_weekly_swim_distance_m.toFixed(0)} m</div>
                    </div>
                  </div>
                  <ResponsiveContainer width="100%" height={180}>
                    <LineChart data={(statistics.weekly_swim_data || []).map(d => ({ ...d, distance: d.distance / 1000 }))}>
                      <XAxis dataKey="week" stroke="#888" fontSize={12} />
                      <YAxis stroke="#888" fontSize={12} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#2a2a2a', border: '1px solid #3a3a3a', borderRadius: '8px' }}
                        labelStyle={{ color: '#e0e0e0' }}
                        formatter={(value) => `${(value * 1000).toFixed(0)} m`}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="distance" 
                        stroke="#00a8cc" 
                        strokeWidth={3} 
                        dot={{ fill: '#00a8cc', r: 4 }} 
                        activeDot={{ r: 6 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                <div className="stat-tile" onClick={() => handleActivityClick('Swim')}>
                  <h3>Swims Completed</h3>
                  <div className="stat-value">{statistics.num_swims} / 84</div>
                  <div className="circular-progress">
                    <ResponsiveContainer width="100%" height={180}>
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'Completed', value: statistics.swim_percentage },
                            { name: 'Remaining', value: 100 - statistics.swim_percentage }
                          ]}
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={70}
                          startAngle={90}
                          endAngle={-270}
                          dataKey="value"
                        >
                          <Cell fill="#00a8cc" />
                          <Cell fill="#2a2a2a" />
                        </Pie>
                        <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" className="progress-text">
                          {statistics.swim_percentage.toFixed(0)}%
                        </text>
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {!loading && !error && !statistics && activities.length === 0 && (
          <div className="no-runs">No runs or swims found for {new Date().getFullYear()}. Click refresh to load data.</div>
        )}
      </main>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>All {selectedActivityType}s - {new Date().getFullYear()}</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <table className="activities-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Name</th>
                    <th>Distance</th>
                    <th>Duration</th>
                    <th>Pace</th>
                    {selectedActivityType === 'Run' && <th>Elevation</th>}
                    <th>Heart Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {detailActivities.map((activity) => (
                    <tr key={activity.id || activity.name}>
                      <td>{activity.date_display || activity.date}</td>
                      <td>{activity.name}</td>
                      <td>{activity.distance}</td>
                      <td>{activity.duration}</td>
                      <td>{formatPace(activity.pace_min, activity.pace_sec, activity.type)}</td>
                      {selectedActivityType === 'Run' && (
                        <td>{activity.elevation_gain_m > 0 ? `${activity.elevation_gain_m} m` : '-'}</td>
                      )}
                      <td>{activity.average_heartrate ? `${activity.average_heartrate} bpm` : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
