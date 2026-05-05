import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import '../styles/Analytics.css';

export default function Analytics() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      const routing = await apiService.getRoutingAnalytics();
      const bandit = await apiService.getBanditMetrics();
      const models = await apiService.getModelComparison();
      
      setMetrics({ routing, bandit, models });
    } catch (err) {
      console.error('Failed to load metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div><p>Loading analytics...</p></div>;
  if (!metrics) return <div><p>No data available</p></div>;

  return (
    <div className="analytics">
      <h2>Analytics Dashboard</h2>

      <div className="analytics-section">
        <h3>Routing Decisions</h3>
        <div className="table">
          <p>Total Decisions: {metrics.routing?.total_decisions || 0}</p>
          <p>Avg Confidence: {((metrics.routing?.avg_confidence || 0) * 100).toFixed(1)}%</p>
        </div>
      </div>

      <div className="analytics-section">
        <h3>Model Performance</h3>
        <table>
          <thead>
            <tr>
              <th>Model</th>
              <th>Count</th>
              <th>Approval Rate</th>
              <th>Accuracy</th>
              <th>Avg Latency (ms)</th>
              <th>Avg Cost</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(metrics.models || {}).map(([model, stats]: any) => (
              <tr key={model}>
                <td>{model}</td>
                <td>{stats.count}</td>
                <td>{stats.approval_rate?.toFixed(1)}%</td>
                <td>{stats.accuracy ? (stats.accuracy * 100).toFixed(1) : 'N/A'}%</td>
                <td>{stats.avg_latency_ms?.toFixed(0)}</td>
                <td>${stats.avg_cost_usd?.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="analytics-section">
        <h3>Contextual Bandit (Self-Improvement)</h3>
        <table>
          <thead>
            <tr>
              <th>Model Arm</th>
              <th>Selections</th>
              <th>Success Rate</th>
              <th>Estimated Reward</th>
              <th>Avg Cost</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(metrics.bandit || {}).map(([model, stat]: any) => (
              <tr key={model}>
                <td>{model}</td>
                <td>{stat.num_selections}</td>
                <td>{(stat.estimated_reward * 100).toFixed(1)}%</td>
                <td>{stat.estimated_reward?.toFixed(3)}</td>
                <td>${stat.avg_cost?.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
