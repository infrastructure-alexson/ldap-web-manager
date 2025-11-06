import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiAlertCircle, FiInfo } from 'react-icons/fi';
import IPAllocationGrid from '../components/IPAllocationGrid';
import Toast from '../components/Toast';
import apiClient from '../api/client';

/**
 * IPAMVisualPage Component
 * 
 * Main page for visualizing and managing IP allocations in a pool.
 * Displays allocations in a grid format with color-coded status.
 */
const IPAMVisualPage = () => {
  const { poolId } = useParams();
  const navigate = useNavigate();

  const [pool, setPool] = useState(null);
  const [allocations, setAllocations] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  // Fetch pool details
  const fetchPoolDetails = useCallback(async () => {
    try {
      const response = await apiClient.get(`/api/ipam/pools/${poolId}`);
      setPool(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load pool details: ' + (err.response?.data?.detail || err.message));
      console.error('Error fetching pool:', err);
    }
  }, [poolId]);

  // Fetch allocations for the pool
  const fetchAllocations = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.get(`/api/ipam/pools/${poolId}/allocations`);
      setAllocations(response.data.items || []);
      setError(null);
    } catch (err) {
      setError('Failed to load allocations: ' + (err.response?.data?.detail || err.message));
      console.error('Error fetching allocations:', err);
    } finally {
      setIsLoading(false);
      setIsInitialLoad(false);
    }
  }, [poolId]);

  // Initial load
  useEffect(() => {
    fetchPoolDetails();
    fetchAllocations();
  }, [fetchPoolDetails, fetchAllocations]);

  // Handle allocation
  const handleAllocate = useCallback(async (allocationId, data) => {
    try {
      await apiClient.post(`/api/ipam/allocations/${allocationId}/allocate`, data);
      setToast({
        type: 'success',
        message: `IP allocated successfully`,
        duration: 3000,
      });
      
      // Refresh allocations
      await fetchAllocations();
    } catch (err) {
      setToast({
        type: 'error',
        message: 'Failed to allocate IP: ' + (err.response?.data?.detail || err.message),
        duration: 5000,
      });
      console.error('Error allocating IP:', err);
    }
  }, [fetchAllocations]);

  // Handle release
  const handleRelease = useCallback(async (allocationId) => {
    try {
      await apiClient.post(`/api/ipam/allocations/${allocationId}/release`);
      setToast({
        type: 'success',
        message: 'IP released successfully',
        duration: 3000,
      });
      
      // Refresh allocations
      await fetchAllocations();
    } catch (err) {
      setToast({
        type: 'error',
        message: 'Failed to release IP: ' + (err.response?.data?.detail || err.message),
        duration: 5000,
      });
      console.error('Error releasing IP:', err);
    }
  }, [fetchAllocations]);

  // Handle refresh
  const handleRefresh = useCallback(() => {
    fetchAllocations();
  }, [fetchAllocations]);

  if (isInitialLoad && isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-4 md:p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <button
            onClick={() => navigate('/ipam')}
            className="p-2 hover:bg-gray-200 rounded-lg transition"
          >
            <FiArrowLeft size={20} />
          </button>
          <h1 className="text-3xl font-bold text-gray-900">IP Pool Visual Manager</h1>
        </div>

        {/* Pool Information */}
        {pool && (
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600">Pool Name</p>
                <p className="text-lg font-semibold text-gray-900">{pool.name}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Network</p>
                <p className="text-lg font-mono text-gray-900">{pool.network}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Gateway</p>
                <p className="text-lg font-mono text-gray-900">{pool.gateway || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">VLAN</p>
                <p className="text-lg font-semibold text-gray-900">{pool.vlan_id || 'N/A'}</p>
              </div>
            </div>

            {pool.description && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-sm text-gray-600">Description</p>
                <p className="text-gray-900">{pool.description}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-8 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <FiAlertCircle className="text-red-600 flex-shrink-0 mt-0.5" size={20} />
          <div>
            <h3 className="font-semibold text-red-900">Error</h3>
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Info Banner */}
      <div className="mb-8 bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
        <FiInfo className="text-blue-600 flex-shrink-0 mt-0.5" size={20} />
        <div className="text-sm text-blue-800">
          <p>
            <strong>Tip:</strong> Click the + button on available IPs to allocate them, or the trash icon on allocated IPs to release them.
          </p>
        </div>
      </div>

      {/* Grid */}
      <IPAllocationGrid
        allocations={allocations}
        pool={pool}
        onAllocate={handleAllocate}
        onRelease={handleRelease}
        onRefresh={handleRefresh}
        isLoading={isLoading}
      />

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

export default IPAMVisualPage;

