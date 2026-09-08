import React, { useState } from 'react';

function ParliamentaryQuery({ apiUrl }) {
  const [formData, setFormData] = useState({
    question: '',
    entities: '',
    metrics: '',
    dateFrom: '',
    dateTo: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [response, setResponse] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.question.trim()) {
      setError('Please enter a question');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const entities = formData.entities
        ? formData.entities.split(',').map((e) => e.trim())
        : null;
      const metrics = formData.metrics
        ? formData.metrics.split(',').map((m) => m.trim())
        : null;

      const res = await fetch(`${apiUrl}/parliamentary-query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: formData.question,
          entities,
          metrics,
          date_range: formData.dateFrom || formData.dateTo
            ? { from: formData.dateFrom, to: formData.dateTo }
            : null,
        }),
      });
      if (!res.ok) throw new Error('Query failed');
      const data = await res.json();
      setResponse(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Parliamentary Query Assistant</h1>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <h2>Parliamentary/High-Priority Query</h2>
        <p style={{ marginBottom: '16px', color: '#6b7280' }}>
          Use this interface to generate official responses to parliamentary and high-priority
          administrative queries with structured evidence and source traceability.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Question *</label>
            <textarea
              name="question"
              value={formData.question}
              onChange={handleChange}
              placeholder="e.g., What was the coal production of Subsidiary X from 2021-22 to 2025-26 compared with annual targets?"
              rows="3"
              disabled={loading}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label>Entities (subsidiaries, mines)</label>
              <input
                type="text"
                name="entities"
                value={formData.entities}
                onChange={handleChange}
                placeholder="e.g., Subsidiary A, Mine 1"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label>Metrics to Extract</label>
              <input
                type="text"
                name="metrics"
                value={formData.metrics}
                onChange={handleChange}
                placeholder="e.g., production, target, achievement"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label>From Year/Date</label>
              <input
                type="text"
                name="dateFrom"
                value={formData.dateFrom}
                onChange={handleChange}
                placeholder="e.g., 2021-22 or 2021-01-01"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label>To Year/Date</label>
              <input
                type="text"
                name="dateTo"
                value={formData.dateTo}
                onChange={handleChange}
                placeholder="e.g., 2025-26 or 2025-12-31"
                disabled={loading}
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ opacity: loading ? 0.6 : 1 }}
          >
            {loading ? 'Processing...' : 'Generate Response'}
          </button>
        </form>
      </div>

      {response && (
        <div className="card">
          <h2>Draft Response</h2>

          <div style={{ marginBottom: '16px' }}>
            <p style={{ color: '#6b7280', fontSize: '13px', marginBottom: '4px' }}>
              Query ID: {response.query_id}
            </p>
          </div>

          <div
            style={{
              backgroundColor: '#f3f4f6',
              padding: '16px',
              borderRadius: '6px',
              marginBottom: '16px',
              border: '1px solid #e5e7eb',
            }}
          >
            <p style={{ fontWeight: 600, marginBottom: '8px' }}>Official Response:</p>
            <p>{response.draft_response}</p>
            <p style={{ marginTop: '12px', fontSize: '13px', color: '#6b7280' }}>
              ✎ Edit this response as needed before approval
            </p>
          </div>

          {response.sources && response.sources.length > 0 && (
            <div style={{ marginBottom: '16px' }}>
              <p style={{ fontWeight: 600, marginBottom: '8px' }}>Sources:</p>
              <div style={{ backgroundColor: '#f9fafb', padding: '12px', borderRadius: '6px' }}>
                <p style={{ fontSize: '13px', color: '#6b7280' }}>
                  {response.sources.length} source(s) referenced
                </p>
              </div>
            </div>
          )}

          <div style={{ display: 'flex', gap: '12px' }}>
            <button className="btn btn-primary" disabled>
              ✓ Approve & Export
            </button>
            <button className="btn btn-secondary">
              📋 Copy to Clipboard
            </button>
          </div>

          <p style={{ marginTop: '12px', fontSize: '13px', color: '#6b7280' }}>
            ℹ️ Full implementation with evidence tables coming in Phase 6
          </p>
        </div>
      )}

      <div className="card">
        <h2>Workflow</h2>
        <ol style={{ marginLeft: '20px', marginTop: '12px' }}>
          <li>Enter your question with entities, metrics, and date range</li>
          <li>System analyzes the query structure</li>
          <li>Relevant documents are retrieved</li>
          <li>Data is extracted and cross-checked</li>
          <li>Draft response is generated</li>
          <li>Evidence table shows supporting data</li>
          <li>Review and edit if needed</li>
          <li>Approve and export as official document</li>
        </ol>
      </div>
    </div>
  );
}

export default ParliamentaryQuery;
