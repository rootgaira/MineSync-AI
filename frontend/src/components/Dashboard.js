import React, { useState, useEffect } from 'react';

function Dashboard({ apiUrl }) {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiUrl}/analytics`);
      if (!response.ok) throw new Error('Failed to fetch analytics');
      const data = await response.json();
      setAnalytics(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        Loading dashboard...
      </div>
    );
  }

  return (
    <div>
      <h1>Dashboard</h1>

      {error && <div className="alert alert-error">{error}</div>}

      {analytics && (
        <>
          <div className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-label">Total Documents</div>
              <div className="kpi-value">{analytics.total_documents}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Processed</div>
              <div className="kpi-value">{analytics.processed_documents}</div>
            </div>
            <div className="kpi-card warning">
              <div className="kpi-label">Failed</div>
              <div className="kpi-value">{analytics.failed_documents}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Extracted Records</div>
              <div className="kpi-value">{analytics.total_extracted_records}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Queries</div>
              <div className="kpi-value">{analytics.total_queries}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Validation Alerts</div>
              <div className="kpi-value">{analytics.validation_alerts}</div>
            </div>
          </div>

          <div className="card">
            <h2>System Status</h2>
            <p>✓ Database connected</p>
            <p>✓ Backend API running</p>
            <p>✓ Ready for document processing</p>
          </div>
        </>
      )}
    </div>
  );
}

export default Dashboard;
