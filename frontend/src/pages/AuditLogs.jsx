/**
 * Audit Logs Viewer Page
 * 
 * Displays and allows filtering of audit logs for compliance and troubleshooting.
 */

import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { auditApi } from '../api/audit';
import { FiSearch, FiDownload, FiFilter, FiBarChart2, FiAlertCircle, FiCheckCircle } from 'react-icons/fi';
import Toast from '../components/Toast';

const AuditLogs = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [search, setSearch] = useState('');
  const [filterAction, setFilterAction] = useState('');
  const [filterResourceType, setFilterResourceType] = useState('');
  const [filterUserId, setFilterUserId] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [toast, setToast] = useState(null);

  // Fetch audit logs
  const { data: logsData, isLoading: logsLoading, error: logsError } = useQuery({
    queryKey: ['audit-logs', page, pageSize, search, filterAction, filterResourceType, filterUserId, filterStatus],
    queryFn: () => auditApi.list({
      page,
      page_size: pageSize,
      search: search || undefined,
      action: filterAction || undefined,
      resource_type: filterResourceType || undefined,
      user_id: filterUserId || undefined,
      status: filterStatus || undefined
    }),
  });

  // Fetch statistics
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['audit-stats'],
    queryFn: () => auditApi.getStatistics(7),
  });

  const handleExport = async (format) => {
    try {
      const blob = await auditApi.export(format, {
        action: filterAction || undefined,
        resource_type: filterResourceType || undefined,
        user_id: filterUserId || undefined,
      });

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `audit-logs-${new Date().toISOString().split('T')[0]}.${format === 'json' ? 'json' : 'csv'}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setToast({
        type: 'success',
        message: `Audit logs exported as ${format.toUpperCase()}`,
        duration: 3000,
      });
    } catch (error) {
      setToast({
        type: 'error',
        message: 'Failed to export audit logs',
        duration: 5000,
      });
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success':
        return 'text-green-600 bg-green-50';
      case 'failure':
        return 'text-yellow-600 bg-yellow-50';
      case 'error':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getActionBadgeColor = (action) => {
    switch (action) {
      case 'CREATE':
        return 'bg-green-100 text-green-800';
      case 'UPDATE':
        return 'bg-blue-100 text-blue-800';
      case 'DELETE':
        return 'bg-red-100 text-red-800';
      case 'READ':
        return 'bg-gray-100 text-gray-800';
      case 'AUTHENTICATION':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Audit Logs</h1>
        <p className="mt-2 text-gray-600">
          View operation history for compliance and troubleshooting
        </p>
      </div>

      {/* Statistics Cards */}
      {stats && !statsLoading && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div className="card">
            <div className="text-sm text-gray-600">Total Logs</div>
            <div className="text-2xl font-bold text-gray-900">{stats.total_logs?.toLocaleString()}</div>
          </div>
          <div className="card">
            <div className="text-sm text-gray-600">Success Rate</div>
            <div className="text-2xl font-bold text-green-600">{stats.success_rate}%</div>
          </div>
          <div className="card">
            <div className="text-sm text-gray-600">Unique Users</div>
            <div className="text-2xl font-bold text-blue-600">{stats.users_count}</div>
          </div>
          <div className="card">
            <div className="text-sm text-gray-600">Failures</div>
            <div className="text-2xl font-bold text-yellow-600">{stats.failure_count}</div>
          </div>
          <div className="card">
            <div className="text-sm text-gray-600">Errors</div>
            <div className="text-2xl font-bold text-red-600">{stats.error_count}</div>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {logsError && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 text-sm">{logsError.message || 'Failed to load audit logs'}</p>
        </div>
      )}

      {/* Search and Filters */}
      <div className="mb-6 space-y-4">
        {/* Search Bar */}
        <div className="card">
          <div className="relative">
            <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search in details, errors, messages..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
          </div>
        </div>

        {/* Filters */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700"
        >
          <FiFilter size={16} />
          {showFilters ? 'Hide Filters' : 'Show Filters'}
        </button>

        {showFilters && (
          <div className="card grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* User Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">User</label>
              <input
                type="text"
                placeholder="Filter by user ID"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={filterUserId}
                onChange={(e) => {
                  setFilterUserId(e.target.value);
                  setPage(1);
                }}
              />
            </div>

            {/* Action Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Action</label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={filterAction}
                onChange={(e) => {
                  setFilterAction(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">All Actions</option>
                <option value="CREATE">Create</option>
                <option value="UPDATE">Update</option>
                <option value="DELETE">Delete</option>
                <option value="READ">Read</option>
                <option value="AUTHENTICATION">Authentication</option>
              </select>
            </div>

            {/* Resource Type Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Resource Type</label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={filterResourceType}
                onChange={(e) => {
                  setFilterResourceType(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">All Types</option>
                <option value="User">User</option>
                <option value="Group">Group</option>
                <option value="ServiceAccount">Service Account</option>
                <option value="DNS">DNS</option>
                <option value="DHCP">DHCP</option>
                <option value="IPAM">IPAM</option>
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={filterStatus}
                onChange={(e) => {
                  setFilterStatus(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">All Status</option>
                <option value="success">Success</option>
                <option value="failure">Failure</option>
                <option value="error">Error</option>
              </select>
            </div>
          </div>
        )}

        {/* Export Buttons */}
        <div className="flex gap-2">
          <button
            onClick={() => handleExport('csv')}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md transition"
          >
            <FiDownload size={16} />
            Export CSV
          </button>
          <button
            onClick={() => handleExport('json')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition"
          >
            <FiDownload size={16} />
            Export JSON
          </button>
        </div>
      </div>

      {/* Audit Logs Table */}
      {logsLoading ? (
        <div className="card text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading audit logs...</p>
        </div>
      ) : logsData?.items?.length === 0 ? (
        <div className="card text-center py-12">
          <FiBarChart2 className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-4 text-gray-600">No audit logs found</p>
          <p className="text-sm text-gray-500">Try adjusting your filters</p>
        </div>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left font-semibold text-gray-900">Timestamp</th>
                <th className="px-6 py-3 text-left font-semibold text-gray-900">User</th>
                <th className="px-6 py-3 text-left font-semibold text-gray-900">Action</th>
                <th className="px-6 py-3 text-left font-semibold text-gray-900">Resource</th>
                <th className="px-6 py-3 text-left font-semibold text-gray-900">Resource ID</th>
                <th className="px-6 py-3 text-left font-semibold text-gray-900">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {logsData?.items?.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-xs text-gray-600">
                      {new Date(log.timestamp).toLocaleString()}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="font-mono text-sm text-gray-900">{log.user_id}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getActionBadgeColor(log.action)}`}>
                      {log.action}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-900">{log.resource_type}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="font-mono text-sm text-gray-600">{log.resource_id || '—'}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      {log.status === 'success' && <FiCheckCircle className="text-green-600" size={16} />}
                      {log.status === 'failure' && <FiAlertCircle className="text-yellow-600" size={16} />}
                      {log.status === 'error' && <FiAlertCircle className="text-red-600" size={16} />}
                      <span className={`text-xs font-semibold capitalize ${getStatusColor(log.status)}`}>
                        {log.status}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {logsData && (
        <div className="mt-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">Items per page:</label>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
              className="px-2 py-1 border border-gray-300 rounded"
            >
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100">100</option>
              <option value="200">200</option>
            </select>
          </div>
          <p className="text-sm text-gray-600">
            Showing {logsData.items?.length || 0} of {logsData.total} logs
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(page + 1)}
              disabled={!logsData.items || logsData.items.length < pageSize}
              className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Toast Notification */}
      {toast && (
        <Toast
          type={toast.type}
          message={toast.message}
          duration={toast.duration}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
};

export default AuditLogs;

