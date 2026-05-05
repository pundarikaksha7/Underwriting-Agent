import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import '../styles/Dashboard.css';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await apiService.getSystemPerformance();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stats');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="dashboard"><p>Loading dashboard...</p></div>;
  if (error) return <div className="dashboard error"><p>Error: {error}</p></div>;
  if (!stats) return <div className="dashboard"><p>No data available</p></div>;

  return (
    <div className="dashboard">
      <h2>Dashboard</h2>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Decisions</h3>
          <p className="stat-value">{stats.total_decisions || 0}</p>
        </div>

        <div className="stat-card">
          <h3>Approval Rate</h3>
          <p className="stat-value">{(stats.approval_rate || 0).toFixed(1)}%</p>
          <p className="stat-detail">
            {stats.approved_count || 0} approved, {stats.rejected_count || 0} rejected
          </p>
        </div>

        <div className="stat-card">
          <h3>Accuracy</h3>
          <p className="stat-value">
            {stats.accuracy ? (stats.accuracy * 100).toFixed(1) : 'N/A'}%
          </p>
          <p className="stat-detail">
            {stats.correct_decisions || 0} correct, {stats.incorrect_decisions || 0} incorrect
          </p>
        </div>

        <div className="stat-card">
          <h3>Avg Latency</h3>
          <p className="stat-value">{(stats.avg_latency_ms || 0).toFixed(0)}ms</p>
        </div>

        <div className="stat-card">
          <h3>Total Cost</h3>
          <p className="stat-value">${(stats.total_cost_usd || 0).toFixed(2)}</p>
          <p className="stat-detail">
            Average: ${(stats.avg_cost_usd || 0).toFixed(4)}
          </p>
        </div>

        <div className="stat-card">
          <h3>Tokens Used</h3>
          <p className="stat-value">{(stats.total_tokens_used || 0).toLocaleString()}</p>
        </div>
      </div>

      <div className="actions">
        <a href="/applications" className="button primary">
          New Application
        </a>
        <a href="/decisions" className="button secondary">
          View Decisions
        </a>
        <a href="/analytics" className="button secondary">
          Analytics
        </a>
      </div>
    </div>
  );
}
