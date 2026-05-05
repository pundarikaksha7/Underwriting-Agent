import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { FiHome, FiFileText, FiCheckCircle, FiBarChart2, FiSettings } from 'react-icons/fi';
import './App.css';
import Dashboard from './pages/Dashboard';
import ApplicationForm from './pages/ApplicationForm';
import DecisionHistory from './pages/DecisionHistory';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';

function App() {
  const [user, setUser] = useState(null);

  return (
    <Router>
      <div className="app">
        <nav className="sidebar">
          <div className="logo">
            <h1>Underwriting Agent</h1>
            <p>AI Decision Intelligence Platform</p>
          </div>
          
          <ul className="nav-links">
            <li>
              <Link to="/">
                <FiHome /> Dashboard
              </Link>
            </li>
            <li>
              <Link to="/applications">
                <FiFileText /> New Application
              </Link>
            </li>
            <li>
              <Link to="/decisions">
                <FiCheckCircle /> Decision History
              </Link>
            </li>
            <li>
              <Link to="/analytics">
                <FiBarChart2 /> Analytics
              </Link>
            </li>
            <li>
              <Link to="/settings">
                <FiSettings /> Settings
              </Link>
            </li>
          </ul>
        </nav>

        <main className="main-content">
          <header className="header">
            <h2>Underwriting Agent</h2>
            <div className="user-section">
              <span>System: v1.0.0</span>
            </div>
          </header>

          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/applications" element={<ApplicationForm />} />
            <Route path="/decisions" element={<DecisionHistory />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
