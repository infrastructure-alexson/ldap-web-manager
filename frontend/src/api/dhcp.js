/**
 * DHCP Management API methods
 */

import apiClient from './client';

export const dhcpApi = {
  // ============================================================================
  // DHCP SUBNETS
  // ============================================================================

  /**
   * List all DHCP subnets
   * @param {Object} params - Query parameters (page, page_size, search)
   * @returns {Promise} Subnet list response
   */
  listSubnets: async (params = {}) => {
    const response = await apiClient.get('/dhcp/subnets', { params });
    return response.data;
  },

  /**
   * Get subnet by ID
   * @param {string} subnetId - Subnet ID
   * @returns {Promise} Subnet object
   */
  getSubnet: async (subnetId) => {
    const response = await apiClient.get(`/dhcp/subnets/${subnetId}`);
    return response.data;
  },

  /**
   * Create new DHCP subnet
   * @param {Object} subnetData - Subnet data
   * @returns {Promise} Created subnet
   */
  createSubnet: async (subnetData) => {
    const response = await apiClient.post('/dhcp/subnets', subnetData);
    return response.data;
  },

  /**
   * Update DHCP subnet
   * @param {string} subnetId - Subnet ID
   * @param {Object} subnetData - Subnet data to update
   * @returns {Promise} Updated subnet
   */
  updateSubnet: async (subnetId, subnetData) => {
    const response = await apiClient.patch(`/dhcp/subnets/${subnetId}`, subnetData);
    return response.data;
  },

  /**
   * Delete DHCP subnet
   * @param {string} subnetId - Subnet ID
   * @returns {Promise}
   */
  deleteSubnet: async (subnetId) => {
    const response = await apiClient.delete(`/dhcp/subnets/${subnetId}`);
    return response.data;
  },

  // ============================================================================
  // DHCP HOSTS (Static Reservations)
  // ============================================================================

  /**
   * List all static hosts in a subnet
   * @param {string} subnetId - Subnet ID
   * @returns {Promise} Host list response
   */
  listHosts: async (subnetId) => {
    const response = await apiClient.get(`/dhcp/subnets/${subnetId}/hosts`);
    return response.data;
  },

  /**
   * Create new static host reservation
   * @param {string} subnetId - Subnet ID
   * @param {Object} hostData - Host data
   * @returns {Promise} Created host
   */
  createHost: async (subnetId, hostData) => {
    const response = await apiClient.post(`/dhcp/subnets/${subnetId}/hosts`, hostData);
    return response.data;
  },

  /**
   * Delete static host reservation
   * @param {string} subnetId - Subnet ID
   * @param {string} hostId - Host ID
   * @returns {Promise}
   */
  deleteHost: async (subnetId, hostId) => {
    const response = await apiClient.delete(`/dhcp/subnets/${subnetId}/hosts/${hostId}`);
    return response.data;
  },

  // ============================================================================
  // DHCP STATISTICS
  // ============================================================================

  /**
   * Get DHCP statistics
   * @returns {Promise} Statistics object
   */
  getStats: async () => {
    const response = await apiClient.get('/dhcp/stats');
    return response.data;
  },
};

