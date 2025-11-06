/**
 * IP Search & Discovery Page
 * 
 * Search and discover IPs across all pools.
 */

import React, { useState } from 'react';
import { FiSearch, FiRefreshCw, FiAlertTriangle, FiDownload } from 'react-icons/fi';
import Toast from '../components/Toast';
import apiClient from '../api/client';

const IPSearch = () => {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState('');
  const [poolFilter, setPoolFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [pools, setPools] = useState([]);
  const [toast, setToast] = useState(null);

  React.useEffect(() => {
    fetchPools();
  }, []);

  const fetchPools = async () => {
    try {
      const response = await apiClient.get('/api/ipam/pools');
      setPools(response.data.pools || []);
    } catch (error) {
      console.error('Error fetching pools:', error);
    }
  };

  const handleSearch = async () => {
    if (!query.trim()) {
      setToast({
        type: 'error',
        message: 'Please enter a search query',
        duration: 3000,
      });
      return;
    }

    setLoading(true);
    try {
      const searchRequest = {
        query: query.trim(),
        search_type: searchType || undefined,
        pool_id: poolFilter ? parseInt(poolFilter) : undefined,
        allocated_only: statusFilter === 'allocated',
        available_only: statusFilter === 'available',
      };

      const response = await apiClient.post('/api/ipam/search', searchRequest);

      setResults(response.data);
      setToast({
        type: 'success',
        message: `Found ${response.data.total} results`,
        duration: 3000,
      });
    } catch (error) {
      setToast({
        type: 'error',
        message: 'Search failed: ' + (error.response?.data?.detail || error.message),
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  };

  const downloadResults = () => {
    if (!results || results.total === 0) return;

    const csv = [
      ['Pool', 'IP Address', 'Hostname', 'Owner', 'Status', 'MAC Address', 'Purpose', 'Allocated At'].join(','),
      ...results.results.map(r =>
        [
          r.pool_name,
          r.ip_address,
          r.hostname || '',
          r.owner || '',
          r.status,
          r.mac_address || '',
          r.purpose || '',
          r.allocated_at || ''
        ].join(',')
      )
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ip-search-results-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const searchTypeOptions = [
    { value: '', label: 'All Fields' },
    { value: 'ip', label: 'IP Address' },
    { value: 'hostname', label: 'Hostname' },
    { value: 'mac', label: 'MAC Address' },
    { value: 'owner', label: 'Owner' },
  ];

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">IP Search & Discovery</h1>
        <p className="mt-2 text-gray-600">
          Search and discover IP addresses across all pools
        </p>
      </div>

      {/* Search Controls */}
      <div className="card mb-6">
        <div className="space-y-4">
          {/* Main Search */}
          <div className="flex gap-4">
            <div className="flex-1">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search by IP, hostname, MAC, or owner..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition flex items-center gap-2"
            >
              <FiSearch size={18} />
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>

          {/* Filters */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Search Type
              </label>
              <select
                value={searchType}
                onChange={(e) => setSearchType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {searchTypeOptions.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>

            {/* Pool Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Filter by Pool
              </label>
              <select
                value={poolFilter}
                onChange={(e) => setPoolFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Pools</option>
                {pools.map(pool => (
                  <option key={pool.id} value={pool.id}>{pool.name}</option>
                ))}
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status Filter
              </label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All</option>
                <option value="allocated">Allocated Only</option>
                <option value="available">Available Only</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Results */}
      {results && (
        <div className="card">
          {/* Summary */}
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Results</h2>
              <p className="text-gray-600">Found {results.total} matching IP addresses</p>
            </div>
            {results.total > 0 && (
              <button
                onClick={downloadResults}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition"
              >
                <FiDownload size={18} />
                Download CSV
              </button>
            )}
          </div>

          {/* Results Table */}
          {results.total === 0 ? (
            <div className="text-center py-12">
              <FiSearch size={48} className="mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500 text-lg">No results found</p>
              <p className="text-gray-400 text-sm mt-1">Try adjusting your search criteria</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-semibold text-gray-900">Pool</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-900">IP Address</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-900">Hostname</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-900">Owner</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-900">Status</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-900">MAC Address</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-900">Purpose</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {results.results.map((result, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-gray-900 font-medium">{result.pool_name}</td>
                      <td className="px-4 py-3 font-mono text-gray-900">{result.ip_address}</td>
                      <td className="px-4 py-3 text-gray-600">{result.hostname || '-'}</td>
                      <td className="px-4 py-3 text-gray-600">{result.owner || '-'}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                          result.status === 'allocated'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {result.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-gray-600 text-xs">{result.mac_address || '-'}</td>
                      <td className="px-4 py-3 text-gray-600">{result.purpose || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Toast */}
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

export default IPSearch;

