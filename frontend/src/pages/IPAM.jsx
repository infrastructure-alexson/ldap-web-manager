/**
 * IPAM Management Page
 * 
 * Displays IP pools and provides access to the visual pool manager.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiPlus, FiSearch, FiGrid, FiEdit, FiTrash2, FiEye } from 'react-icons/fi';
import apiClient from '../api/client';
import Toast from '../components/Toast';

const IPAM = () => {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [pools, setPools] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);
  const navigate = useNavigate();

  // Fetch pools
  const fetchPools = async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.get('/api/ipam/pools', {
        params: {
          page,
          page_size: 20,
          search: search || undefined,
        },
      });
      setPools(response.data.items || []);
      setError(null);
    } catch (err) {
      setError('Failed to load pools: ' + (err.response?.data?.detail || err.message));
      console.error('Error fetching pools:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPools();
  }, [page, search]);

  const handleSearch = (e) => {
    setSearch(e.target.value);
    setPage(1);
  };

  const handleDeletePool = async (poolId) => {
    if (!window.confirm('Are you sure you want to delete this pool? This cannot be undone.')) {
      return;
    }

    try {
      await apiClient.delete(`/api/ipam/pools/${poolId}`);
      setToast({
        type: 'success',
        message: 'Pool deleted successfully',
        duration: 3000,
      });
      fetchPools();
    } catch (err) {
      setToast({
        type: 'error',
        message: 'Failed to delete pool: ' + (err.response?.data?.detail || err.message),
        duration: 5000,
      });
    }
  };

  const calculateUtilization = (pool) => {
    if (!pool.total_ips) return 0;
    return Math.round((pool.used_ips / pool.total_ips) * 100);
  };

  const getUtilizationColor = (utilization) => {
    if (utilization < 50) return 'bg-green-500';
    if (utilization < 80) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">IPAM Management</h1>
          <p className="mt-2 text-gray-600">
            Manage IP address pools and allocations
          </p>
        </div>
        <button 
          onClick={() => navigate('/ipam/create')}
          className="btn-primary flex items-center"
        >
          <FiPlus className="mr-2" />
          Create Pool
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {/* Search */}
      <div className="mb-6 card">
        <div className="relative">
          <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search pools by name or network..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={search}
            onChange={handleSearch}
          />
        </div>
      </div>

      {/* Pools Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      ) : pools.length === 0 ? (
        <div className="card text-center py-12">
          <FiGrid className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-4 text-gray-600">No IP pools found</p>
          <p className="text-sm text-gray-500">Create a new pool to get started</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {pools.map((pool) => {
            const utilization = calculateUtilization(pool);
            return (
              <div key={pool.id} className="card hover:shadow-lg transition">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{pool.name}</h3>
                    <p className="text-sm text-gray-500 font-mono">{pool.network}</p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => navigate(`/ipam/pools/${pool.id}/visual`)}
                      className="p-2 hover:bg-blue-50 rounded-lg transition text-blue-600"
                      title="Visual Manager"
                    >
                      <FiEye size={18} />
                    </button>
                    <button
                      onClick={() => navigate(`/ipam/pools/${pool.id}/edit`)}
                      className="p-2 hover:bg-gray-100 rounded-lg transition"
                      title="Edit"
                    >
                      <FiEdit size={18} />
                    </button>
                    <button
                      onClick={() => handleDeletePool(pool.id)}
                      className="p-2 hover:bg-red-50 rounded-lg transition text-red-600"
                      title="Delete"
                    >
                      <FiTrash2 size={18} />
                    </button>
                  </div>
                </div>

                {/* Description */}
                {pool.description && (
                  <p className="text-sm text-gray-600 mb-4">{pool.description}</p>
                )}

                {/* Details */}
                <div className="space-y-2 mb-4 text-sm">
                  {pool.gateway && (
                    <div className="flex justify-between text-gray-600">
                      <span>Gateway:</span>
                      <span className="font-mono">{pool.gateway}</span>
                    </div>
                  )}
                  {pool.vlan_id && (
                    <div className="flex justify-between text-gray-600">
                      <span>VLAN:</span>
                      <span className="font-mono">{pool.vlan_id}</span>
                    </div>
                  )}
                  {pool.dns_servers && pool.dns_servers.length > 0 && (
                    <div className="flex justify-between text-gray-600">
                      <span>DNS Servers:</span>
                      <span className="font-mono text-right">{pool.dns_servers.join(', ')}</span>
                    </div>
                  )}
                </div>

                {/* Utilization */}
                <div className="border-t border-gray-200 pt-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">Utilization</span>
                    <span className="text-sm font-semibold text-gray-900">
                      {pool.used_ips} / {pool.total_ips}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${getUtilizationColor(utilization)}`}
                      style={{ width: `${utilization}%` }}
                    />
                  </div>
                  <div className="text-right mt-1">
                    <span className="text-xs font-semibold text-gray-600">{utilization}%</span>
                  </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-2 mt-4 text-center text-xs border-t border-gray-200 pt-4">
                  <div>
                    <p className="text-gray-500">Available</p>
                    <p className="font-bold text-green-600">{pool.available_ips}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Allocated</p>
                    <p className="font-bold text-blue-600">{pool.used_ips}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Total</p>
                    <p className="font-bold text-gray-600">{pool.total_ips}</p>
                  </div>
                </div>
              </div>
            );
          })}
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

export default IPAM;

