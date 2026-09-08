import React, { useState, useEffect } from 'react';

function Analytics({ apiUrl }) {
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
        Loading analytics...
      </div>
    );
  }

  return (
    <div>
      <h1>Analytics Dashboard</h1>

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
              <div className="kpi-label">Total Queries</div>
              <div className="kpi-value">{analytics.total_queries}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Reports Generated</div>
              <div className="kpi-value">{analytics.total_reports}</div>
            </div>
            <div className="kpi-card warning">
              <div className="kpi-label">Validation Alerts</div>
              <div className="kpi-value">{analytics.validation_alerts}</div>
            </div>
          </div>

          <div className="card">
            <h2>Processing Summary</h2>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <p style={{ color: '#6b7280', marginBottom: '8px' }}>Success Rate</p>
                <div
                  style={{
                    fontSize: '24px',
                    fontWeight: 700,
                    color: '#16a34a',
                  }}
                >
                  {analytics.total_documents > 0
                    ? Math.round(
                        (analytics.processed_documents / analytics.total_documents) * 100
                      )
                    : 0}
                  %
                </div>
              </div>
              <div>
                <p style={{ color: '#6b7280', marginBottom: '8px' }}>
                  Extraction Accuracy (Phase 3+)
                </p>
                <div style={{ fontSize: '24px', fontWeight: 700, color: '#1e40af' }}>
                  95%
                </div>
                <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                  Target threshold
                </p>
              </div>
            </div>
          </div>

          <div className="card">
            <h2>Production Metrics (Phase 3+)</h2>
            <p style={{ color: '#6b7280', marginBottom: '12px' }}>
              These metrics will be populated once document processing and extraction are
              implemented.
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div
                style={{
                  padding: '12px',
                  backgroundColor: '#f3f4f6',
                  borderRadius: '6px',
                }}
              >
                <p style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>
                  Total Production
                </p>
                <p style={{ fontSize: '20px', fontWeight: 600 }}>
                  {analytics.production_total ? `${analytics.production_total} MT` : '—'}
                </p>
              </div>
              <div
                style={{
                  padding: '12px',
                  backgroundColor: '#f3f4f6',
                  borderRadius: '6px',
                }}
              >
                <p style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>
                  Total Target
                </p>
                <p style={{ fontSize: '20px', fontWeight: 600 }}>
                  {analytics.target_total ? `${analytics.target_total} MT` : '—'}
                </p>
              </div>
            </div>
          </div>

          <div className="card">
            <h2>Feature Implementation Timeline</h2>
            <div style={{ marginTop: '12px' }}>
              <div style={{ marginBottom: '16px' }}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: '4px',
                  }}
                >
                  <span style={{ fontSize: '16px', marginRight: '8px' }}>✓</span>
                  <p style={{ fontWeight: 600 }}>Phase 1: Basic Setup (Current)</p>
                </div>
                <p style={{ color: '#6b7280', fontSize: '13px', marginLeft: '24px' }}>
                  Document upload, React/FastAPI, PostgreSQL
                </p>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: '4px',
                  }}
                >
                  <span style={{ fontSize: '16px', marginRight: '8px' }}>⏳</span>
                  <p style={{ fontWeight: 600 }}>Phase 2: OCR & Document Processing</p>
                </div>
                <p style={{ color: '#6b7280', fontSize: '13px', marginLeft: '24px' }}>
                  Tesseract, PaddleOCR, text extraction, document metadata
                </p>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: '4px',
                  }}
                >
                  <span style={{ fontSize: '16px', marginRight: '8px' }}>⏳</span>
                  <p style={{ fontWeight: 600 }}>Phase 3: AI Data Extraction</p>
                </div>
                <p style={{ color: '#6b7280', fontSize: '13px', marginLeft: '24px' }}>
                  Structured extraction, JSON storage, local LLM
                </p>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: '4px',
                  }}
                >
                  <span style={{ fontSize: '16px', marginRight: '8px' }}>⏳</span>
                  <p style={{ fontWeight: 600 }}>Phases 4-8: Validation, RAG, Reports, etc.</p>
                </div>
                <p style={{ color: '#6b7280', fontSize: '13px', marginLeft: '24px' }}>
                  Full data validation, semantic search, parliamentary queries, analytics
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default Analytics;
