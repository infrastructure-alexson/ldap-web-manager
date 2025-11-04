/**
 * DNS Management API methods
 */

import apiClient from './client';

export const dnsApi = {
  // ============================================================================
  // DNS ZONES
  // ============================================================================

  /**
   * List all DNS zones
   * @param {Object} params - Query parameters (page, page_size, search)
   * @returns {Promise} Zone list response
   */
  listZones: async (params = {}) => {
    const response = await apiClient.get('/dns/zones', { params });
    return response.data;
  },

  /**
   * Get zone by name
   * @param {string} zoneName - Zone name
   * @returns {Promise} Zone object
   */
  getZone: async (zoneName) => {
    const response = await apiClient.get(`/dns/zones/${zoneName}`);
    return response.data;
  },

  /**
   * Create new DNS zone
   * @param {Object} zoneData - Zone data
   * @returns {Promise} Created zone
   */
  createZone: async (zoneData) => {
    const response = await apiClient.post('/dns/zones', zoneData);
    return response.data;
  },

  /**
   * Update DNS zone
   * @param {string} zoneName - Zone name
   * @param {Object} zoneData - Zone data to update
   * @returns {Promise} Updated zone
   */
  updateZone: async (zoneName, zoneData) => {
    const response = await apiClient.patch(`/dns/zones/${zoneName}`, zoneData);
    return response.data;
  },

  /**
   * Delete DNS zone
   * @param {string} zoneName - Zone name
   * @returns {Promise}
   */
  deleteZone: async (zoneName) => {
    const response = await apiClient.delete(`/dns/zones/${zoneName}`);
    return response.data;
  },

  // ============================================================================
  // DNS RECORDS
  // ============================================================================

  /**
   * List all records in a zone
   * @param {string} zoneName - Zone name
   * @returns {Promise} Record list response
   */
  listRecords: async (zoneName) => {
    const response = await apiClient.get(`/dns/zones/${zoneName}/records`);
    return response.data;
  },

  /**
   * Create new DNS record
   * @param {string} zoneName - Zone name
   * @param {Object} recordData - Record data
   * @returns {Promise} Created record
   */
  createRecord: async (zoneName, recordData) => {
    const response = await apiClient.post(`/dns/zones/${zoneName}/records`, recordData);
    return response.data;
  },

  /**
   * Update DNS record
   * @param {string} zoneName - Zone name
   * @param {string} recordName - Record name
   * @param {string} recordType - Record type
   * @param {Object} recordData - Record data to update
   * @returns {Promise} Updated record
   */
  updateRecord: async (zoneName, recordName, recordType, recordData) => {
    const response = await apiClient.patch(
      `/dns/zones/${zoneName}/records/${recordName}/${recordType}`,
      recordData
    );
    return response.data;
  },

  /**
   * Delete DNS record
   * @param {string} zoneName - Zone name
   * @param {string} recordName - Record name
   * @param {string} recordType - Record type
   * @returns {Promise}
   */
  deleteRecord: async (zoneName, recordName, recordType) => {
    const response = await apiClient.delete(
      `/dns/zones/${zoneName}/records/${recordName}/${recordType}`
    );
    return response.data;
  },
};

