/**
 * IPAM API Service
 * 
 * Provides API methods for IPAM operations including pool and allocation management.
 */

import client from './client';

export const ipamApi = {
  /**
   * List IP pools
   */
  listPools: (params = {}) =>
    client.get('/api/ipam/pools', { params }),

  /**
   * Get a specific IP pool
   */
  getPool: (poolId) =>
    client.get(`/api/ipam/pools/${poolId}`),

  /**
   * Create a new IP pool
   */
  createPool: (data) =>
    client.post('/api/ipam/pools', data),

  /**
   * Update an IP pool
   */
  updatePool: (poolId, data) =>
    client.patch(`/api/ipam/pools/${poolId}`, data),

  /**
   * Delete an IP pool
   */
  deletePool: (poolId) =>
    client.delete(`/api/ipam/pools/${poolId}`),

  /**
   * Get IPAM statistics
   */
  getStats: () =>
    client.get('/api/ipam/stats'),

  /**
   * List allocations in a pool
   */
  listAllocations: (poolId, params = {}) =>
    client.get(`/api/ipam/pools/${poolId}/allocations`, { params }),

  /**
   * Get a specific IP allocation
   */
  getAllocation: (allocationId) =>
    client.get(`/api/ipam/allocations/${allocationId}`),

  /**
   * Allocate an IP address
   */
  allocateIP: (allocationId, data) =>
    client.post(`/api/ipam/allocations/${allocationId}/allocate`, data),

  /**
   * Release an IP address
   */
  releaseIP: (allocationId) =>
    client.post(`/api/ipam/allocations/${allocationId}/release`),

  /**
   * Search for IP addresses
   */
  searchIPs: (params = {}) =>
    client.get('/api/ipam/search', { params }),

  /**
   * Get utilization report
   */
  getUtilizationReport: (poolId) =>
    client.get(`/api/ipam/pools/${poolId}/utilization`),

  /**
   * Export allocations
   */
  exportAllocations: (poolId, format = 'csv') =>
    client.get(`/api/ipam/pools/${poolId}/export`, {
      params: { format },
      responseType: 'blob',
    }),

  /**
   * Import allocations from CSV
   */
  importAllocations: (poolId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return client.post(`/api/ipam/pools/${poolId}/import`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export default ipamApi;

