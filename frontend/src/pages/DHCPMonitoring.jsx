import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { FiAlertTriangle, FiCheckCircle, FiTrendingUp, FiRefreshCw } from 'react-icons/fi';
import apiClient from '../api/client';

export default function DHCPMonitoring() {
  const [filters, setFilters] = useState({
    subnet: '',
    status: '',
    host: '',
  });
  const [pagination, setPagination] = useState({ skip: 0, limit: 20 });

  // Fetch DHCP statistics
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery(
    'dhcpStats',
    async () => {
      const response = await apiClient.get('/dhcp/statistics');
      return response.data;
    },
    { refetchInterval: 30000 } // Refresh every 30 seconds
  );

  // Fetch DHCP leases
  const { data: leases, isLoading: leasesLoading, refetch: refetchLeases } = useQuery(
    ['dhcpLeases', filters, pagination],
    async () => {
      const params = new URLSearchParams({
        skip: pagination.skip,
        limit: pagination.limit,
        ...Object.fromEntries(Object.entries(filters).filter(([, v]) => v)),
      });
      const response = await apiClient.get(`/dhcp/leases?${params}`);
      return response.data;
    }
  );

  // Fetch DHCP alerts
  const { data: alerts, refetch: refetchAlerts } = useQuery(
    'dhcpAlerts',
    async () => {
      const response = await apiClient.get('/dhcp/alerts');
      return response.data;
    },
    { refetchInterval: 60000 } // Refresh every 60 seconds
  );

  const handleRefresh = () => {
    refetchStats();
    refetchLeases();
    refetchAlerts();
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setPagination({ skip: 0, limit: 20 });
  };

  const handlePageChange = (newSkip) => {
    setPagination(prev => ({ ...prev, skip: newSkip }));
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-600';
      case 'expired': return 'text-red-600';
      case 'reserved': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  const getAlertColor = (severity) => {
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
        <h1 className="text-3xl font-bold">DHCP Lease Monitoring</h1>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          <FiRefreshCw size={18} />
          Refresh
        </button>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Active Leases</p>
                <p className="text-2xl font-bold">{stats.active_leases}</p>
              </div>
              <FiCheckCircle size={32} className="text-green-500" />
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Utilization</p>
                <p className="text-2xl font-bold">{stats.utilization_percent}%</p>
              </div>
              <FiTrendingUp size={32} className="text-blue-500" />
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Expiring Soon</p>
                <p className="text-2xl font-bold">{stats.expiring_soon}</p>
              </div>
              <FiAlertTriangle size={32} className="text-yellow-500" />
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Alerts</p>
                <p className="text-2xl font-bold">{stats.alerts}</p>
              </div>
              <FiAlertTriangle size={32} className={stats.alerts > 0 ? 'text-red-500' : 'text-gray-500'} />
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
              <div key={idx} className={`p-3 border rounded ${getAlertColor(alert.severity)}`}>
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-semibold">{alert.type}</p>
                    <p>{alert.message}</p>
                    <p className="text-sm opacity-75">{alert.ip_address} ({alert.hostname})</p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${alert.severity === 'critical' ? 'bg-red-500 text-white' : alert.severity === 'warning' ? 'bg-yellow-500 text-white' : 'bg-blue-500 text-white'}`}>
                    {alert.severity.toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h2 className="text-lg font-bold mb-4">Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <input
            type="text"
            placeholder="Subnet (e.g., 192.168.1.0/24)"
            value={filters.subnet}
            onChange={(e) => handleFilterChange('subnet', e.target.value)}
            className="px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={filters.status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
            className="px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="expired">Expired</option>
            <option value="reserved">Reserved</option>
          </select>
          <input
            type="text"
            placeholder="Search by IP or hostname"
            value={filters.host}
            onChange={(e) => handleFilterChange('host', e.target.value)}
            className="px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Leases Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold">IP Address</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">Hostname</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">MAC Address</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">Subnet</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">Status</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">Days Left</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">Expiration</th>
              </tr>
            </thead>
            <tbody>
              {leasesLoading ? (
                <tr>
                  <td colSpan="7" className="px-6 py-4 text-center text-gray-500">Loading...</td>
                </tr>
              ) : leases && leases.leases && leases.leases.length > 0 ? (
                leases.leases.map((lease, idx) => (
                  <tr key={idx} className="border-t hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-mono">{lease.ip_address}</td>
                    <td className="px-6 py-4 text-sm">{lease.hostname}</td>
                    <td className="px-6 py-4 text-sm font-mono text-xs">{lease.mac_address}</td>
                    <td className="px-6 py-4 text-sm">{lease.subnet}</td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${getStatusColor(lease.status)}`}>
                        {lease.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm font-bold">
                      <span className={lease.days_remaining < 3 ? 'text-red-600' : lease.days_remaining < 7 ? 'text-yellow-600' : 'text-green-600'}>
                        {lease.days_remaining}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {new Date(lease.lease_end).toLocaleDateString()} {new Date(lease.lease_end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" className="px-6 py-4 text-center text-gray-500">No leases found</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {leases && (
          <div className="px-6 py-4 border-t flex justify-between items-center">
            <div className="text-sm text-gray-600">
              Showing {pagination.skip + 1}-{Math.min(pagination.skip + pagination.limit, leases.total)} of {leases.total}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handlePageChange(Math.max(0, pagination.skip - pagination.limit))}
                disabled={pagination.skip === 0}
                className="px-3 py-2 border rounded disabled:opacity-50 hover:bg-gray-100"
              >
                Previous
              </button>
              <button
                onClick={() => handlePageChange(pagination.skip + pagination.limit)}
                disabled={pagination.skip + pagination.limit >= leases.total}
                className="px-3 py-2 border rounded disabled:opacity-50 hover:bg-gray-100"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

