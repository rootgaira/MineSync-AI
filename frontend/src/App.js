import React, { useState, useEffect } from 'react';
import './App.css';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import Documents from './components/Documents';
import AIQuery from './components/AIQuery';
import ParliamentaryQuery from './components/ParliamentaryQuery';
import Analytics from './components/Analytics';

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [apiUrl] = useState('http://localhost:8000');

  return (
    <div className="App">
      <div className="app-container">
        <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} />
        <main className="main-content">
          {currentPage === 'dashboard' && <Dashboard apiUrl={apiUrl} />}
          {currentPage === 'documents' && <Documents apiUrl={apiUrl} />}
          {currentPage === 'ai-query' && <AIQuery apiUrl={apiUrl} />}
          {currentPage === 'parliamentary-query' && <ParliamentaryQuery apiUrl={apiUrl} />}
          {currentPage === 'analytics' && <Analytics apiUrl={apiUrl} />}
        </main>
      </div>
    </div>
  );
}

export default App;
