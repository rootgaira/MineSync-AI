import React, { useState } from 'react';

function AIQuery({ apiUrl }) {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [response, setResponse] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${apiUrl}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_question: question,
          query_type: 'standard',
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
      <h1>AI Query</h1>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <h2>Ask a Question</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Your Question</label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g., What was the coal production in FY 2025-26?"
              rows="4"
              disabled={loading}
            />
          </div>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ opacity: loading ? 0.6 : 1 }}
          >
            {loading ? 'Processing...' : 'Submit Query'}
          </button>
        </form>
      </div>

      {response && (
        <div className="card">
          <h2>Query Result</h2>
          <div style={{ marginBottom: '12px' }}>
            <p style={{ color: '#6b7280', fontSize: '13px', marginBottom: '4px' }}>
              Query ID: {response.id}
            </p>
            <p style={{ color: '#6b7280', fontSize: '13px' }}>
              Created: {new Date(response.created_at).toLocaleString()}
            </p>
          </div>
          <div
            style={{
              backgroundColor: '#f0f4ff',
              padding: '12px',
              borderRadius: '6px',
              marginBottom: '12px',
            }}
          >
            <p style={{ fontWeight: 600, marginBottom: '4px' }}>Your Question:</p>
            <p>{response.user_question}</p>
          </div>
          <p style={{ color: '#6b7280', fontSize: '13px' }}>
            💡 Response generation will be implemented in Phase 5 (RAG & LLM integration)
          </p>
        </div>
      )}

      <div className="card">
        <h2>About AI Query</h2>
        <p>
          The AI Query feature allows you to ask natural language questions about your mining
          documents. The system will:
        </p>
        <ul style={{ marginLeft: '20px', marginTop: '12px' }}>
          <li>Understand your question</li>
          <li>Search relevant documents using semantic retrieval</li>
          <li>Extract structured data from the documents</li>
          <li>Generate an answer with source citations</li>
          <li>Show confidence levels and validation status</li>
        </ul>
        <p style={{ marginTop: '12px', color: '#6b7280', fontSize: '13px' }}>
          ℹ️ Full implementation coming in Phase 5
        </p>
      </div>
    </div>
  );
}

export default AIQuery;
