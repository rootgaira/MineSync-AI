import React, { useState, useEffect } from 'react';

function Documents({ apiUrl }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [documentType, setDocumentType] = useState('production_report');
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiUrl}/documents?skip=0&limit=100`);
      if (!response.ok) throw new Error('Failed to fetch documents');
      const data = await response.json();
      setDocuments(data.documents);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    setSelectedFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('document_type', documentType);

    try {
      setUploading(true);
      setError(null);
      const response = await fetch(`${apiUrl}/documents/upload?document_type=${documentType}`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error('Upload failed');
      const newDoc = await response.json();
      setDocuments([newDoc, ...documents]);
      setSelectedFile(null);
      document.getElementById('fileInput').value = '';
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'processed':
        return 'badge-success';
      case 'processing':
        return 'badge-info';
      case 'failed':
        return 'badge-error';
      default:
        return 'badge-warning';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div>
      <h1>Document Management</h1>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <h2>Upload Document</h2>
        <div className="form-group">
          <label>Document Type</label>
          <select
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value)}
          >
            <option value="production_report">Production Report</option>
            <option value="geological_report">Geological Report</option>
            <option value="annual_report">Annual Report</option>
            <option value="project_report">Project Report</option>
            <option value="administrative_document">Administrative Document</option>
          </select>
        </div>

        <div className="file-upload" onClick={() => document.getElementById('fileInput').click()}>
          <input
            id="fileInput"
            type="file"
            onChange={handleFileSelect}
            accept=".pdf,.docx,.xlsx,.png,.jpg,.jpeg"
          />
          <div style={{ marginBottom: '8px', fontSize: '24px' }}>📁</div>
          {selectedFile ? (
            <div>
              <p style={{ fontWeight: 600, marginBottom: '4px' }}>{selectedFile.name}</p>
              <p style={{ fontSize: '12px', color: '#6b7280' }}>
                {formatFileSize(selectedFile.size)}
              </p>
            </div>
          ) : (
            <div>
              <p style={{ fontWeight: 600, marginBottom: '4px' }}>
                Click to upload or drag and drop
              </p>
              <p style={{ fontSize: '12px', color: '#6b7280' }}>
                PDF, DOCX, XLSX, PNG, JPG (Max 100MB)
              </p>
            </div>
          )}
        </div>

        <button
          className="btn btn-primary"
          onClick={handleUpload}
          disabled={uploading || !selectedFile}
          style={{ marginTop: '12px', opacity: uploading || !selectedFile ? 0.6 : 1 }}
        >
          {uploading ? 'Uploading...' : 'Upload Document'}
        </button>
      </div>

      <div className="card">
        <h2>Documents ({documents.length})</h2>
        {loading ? (
          <div className="loading">
            <div className="spinner"></div>
            Loading documents...
          </div>
        ) : documents.length === 0 ? (
          <p style={{ color: '#6b7280' }}>No documents uploaded yet.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Filename</th>
                <th>Type</th>
                <th>Size</th>
                <th>Status</th>
                <th>Uploaded</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id}>
                  <td>{doc.filename}</td>
                  <td>{doc.document_type}</td>
                  <td>{formatFileSize(doc.file_size)}</td>
                  <td>
                    <span className={`badge ${getStatusBadgeClass(doc.status)}`}>
                      {doc.status}
                    </span>
                  </td>
                  <td>
                    {new Date(doc.upload_date).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default Documents;
