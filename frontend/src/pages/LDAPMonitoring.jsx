import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { FiAlertTriangle, FiCheckCircle, FiRefreshCw, FiActivity, FiServer } from 'react-icons/fi';
import apiClient from '../api/client';

export default function LDAPMonitoring() {
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch LDAP health
  const { data: health, isLoading: healthLoading, refetch: refetchHealth } = useQuery(
    'ldapHealth',
    async () => {
      const response = await apiClient.get('/ldap/health');
      return response.data;
    },
    { 
      refetchInterval: autoRefresh ? 30000 : false,
      staleTime: 10000,
    }
  );

  // Fetch summary
  const { data: summary, refetch: refetchSummary } = useQuery(
    'ldapSummary',
    async () => {
      const response = await apiClient.get('/ldap/summary');
      return response.data;
    },
    { 
      refetchInterval: autoRefresh ? 60000 : false,
      staleTime: 10000,
    }
  );

  // Fetch performance metrics
  const { data: performance, refetch: refetchPerformance } = useQuery(
    'ldapPerformance',
    async () => {
      const response = await apiClient.get('/ldap/performance');
      return response.data;
    },
    { 
      refetchInterval: autoRefresh ? 60000 : false,
      staleTime: 10000,
    }
  );

  // Fetch alerts
  const { data: alerts, refetch: refetchAlerts } = useQuery(
    'ldapAlerts',
    async () => {
      const response = await apiClient.get('/ldap/alerts');
      return response.data;
    },
    { 
      refetchInterval: autoRefresh ? 30000 : false,
      staleTime: 10000,
    }
  );

  // Fetch replication status
  const { data: replication } = useQuery(
    'ldapReplication',
    async () => {
      const response = await apiClient.get('/ldap/replication');
      return response.data;
    },
    { 
      refetchInterval: autoRefresh ? 60000 : false,
      staleTime: 10000,
    }
  );

  const handleRefresh = () => {
    refetchHealth();
    refetchSummary();
    refetchPerformance();
    refetchAlerts();
  };

  const getStatusColor = (isOnline) => {
    return isOnline ? 'text-green-600' : 'text-red-600';
  };

  const getAlertBgColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 border-red-400 text-red-800';
      case 'warning': return 'bg-yellow-100 border-yellow-400 text-yellow-800';
      default: return 'bg-blue-100 border-blue-400 text-blue-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">LDAP Server Monitoring</h1>
        <div className="flex gap-2">
          <label className="flex items-center gap-2 px-4 py-2 bg-gray-200 rounded hover:bg-gray-300">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm font-medium">Auto Refresh</span>
          </label>
          <button
            onClick={handleRefresh}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            <FiRefreshCw size={18} />
            Refresh
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Servers Online</p>
                <p className="text-2xl font-bold">{summary.servers_online}/{summary.servers_total}</p>
              </div>
              <FiServer size={32} className={summary.servers_offline === 0 ? 'text-green-500' : 'text-red-500'} />
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Replication</p>
                <p className="text-2xl font-bold">{summary.replication_healthy ? 'Healthy' : 'Issues'}</p>
              </div>
              <FiCheckCircle size={32} className={summary.replication_healthy ? 'text-green-500' : 'text-red-500'} />
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Success Rate</p>
                <p className="text-2xl font-bold">{summary.success_rate.toFixed(1)}%</p>
              </div>
              <FiActivity size={32} className="text-blue-500" />
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Active Alerts</p>
                <p className="text-2xl font-bold">{summary.active_alerts}</p>
              </div>
              <FiAlertTriangle size={32} className={summary.active_alerts > 0 ? 'text-red-500' : 'text-gray-500'} />
            </div>
          </div>
        </div>
      )}

      {/* Alerts Section */}
      {alerts && alerts.length > 0 && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h2 className="text-lg font-bold mb-4">Active Alerts</h2>
          <div className="space-y-2">
            {alerts.map((alert, idx) => (
              <div key={idx} className={`p-3 border rounded ${getAlertBgColor(alert.severity)}`}>
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-semibold">{alert.type.replace('_', ' ').toUpperCase()}</p>
                    <p>{alert.message}</p>
                    <p className="text-sm opacity-75">Server: {alert.server}</p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${
                    alert.severity === 'critical' ? 'bg-red-500 text-white' :
                    alert.severity === 'warning' ? 'bg-yellow-500 text-white' :
                    'bg-blue-500 text-white'
                  }`}>
                    {alert.severity.toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Server Status */}
      {health && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Primary Server */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
              <FiServer size={20} />
              Primary Server
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Hostname:</span>
                <span className="font-mono text-sm">{health.primary_server.hostname}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Status:</span>
                <span className={`font-bold ${getStatusColor(health.primary_server.is_online)}`}>
                  {health.primary_server.is_online ? 'Online' : 'Offline'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Response Time:</span>
                <span className="font-mono text-sm">{health.primary_server.response_time_ms.toFixed(2)}ms</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">IP Address:</span>
                <span className="font-mono text-sm">{health.primary_server.ip_address}</span>
              </div>
            </div>
          </div>

          {/* Secondary Server */}
          {health.secondary_server && (
            <div className="bg-white p-4 rounded-lg shadow">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                <FiServer size={20} />
                Secondary Server
              </h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Hostname:</span>
                  <span className="font-mono text-sm">{health.secondary_server.hostname}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Status:</span>
                  <span className={`font-bold ${getStatusColor(health.secondary_server.is_online)}`}>
                    {health.secondary_server.is_online ? 'Online' : 'Offline'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Response Time:</span>
                  <span className="font-mono text-sm">{health.secondary_server.response_time_ms.toFixed(2)}ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">IP Address:</span>
                  <span className="font-mono text-sm">{health.secondary_server.ip_address}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Replication Status */}
      {replication && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-bold mb-4">Replication Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex justify-between">
              <span className="text-gray-600">From:</span>
              <span className="font-mono text-sm">{replication.server_from}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">To:</span>
              <span className="font-mono text-sm">{replication.server_to}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Status:</span>
              <span className={`font-bold ${replication.status === 'in_sync' ? 'text-green-600' : 'text-red-600'}`}>
                {replication.status.replace('_', ' ').toUpperCase()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Replication Lag:</span>
              <span className="font-mono text-sm">{replication.replication_lag_seconds.toFixed(2)}s</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Last Sync:</span>
              <span className="font-mono text-sm">{new Date(replication.last_sync).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Changes Replicated:</span>
              <span className="font-mono text-sm">{replication.total_changes_replicated}</span>
            </div>
          </div>
        </div>
      )}

      {/* Performance Metrics */}
      {performance && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-bold mb-4">Performance Metrics</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-gray-600 text-sm">Avg Response Time</p>
              <p className="text-2xl font-bold">{performance.avg_response_time_ms.toFixed(2)}ms</p>
            </div>
            <div>
              <p className="text-gray-600 text-sm">Total Queries</p>
              <p className="text-2xl font-bold">{performance.total_queries.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-gray-600 text-sm">Success Rate</p>
              <p className="text-2xl font-bold">{performance.success_rate.toFixed(1)}%</p>
            </div>
          </div>

          {/* Query Breakdown */}
          <div className="mt-4 space-y-2">
            <p className="font-semibold text-sm">Query Performance Breakdown:</p>
            {performance.query_performance.map((qp, idx) => (
              <div key={idx} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                <span className="text-sm font-mono">{qp.query_type}</span>
                <div className="flex gap-4 text-sm">
                  <span>Avg: {qp.avg_latency_ms.toFixed(2)}ms</span>
                  <span>Count: {qp.count.toLocaleString()}</span>
                  <span className="text-red-600">Failures: {(qp.failure_rate).toFixed(2)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

