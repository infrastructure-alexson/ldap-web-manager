/**
 * Audit Logs API Service
 * 
 * Provides API methods for viewing and querying audit logs.
 */

import client from './client';

export const auditApi = {
  /**
   * List audit logs with filtering and pagination
   */
  list: (params = {}) =>
    client.get('/api/audit', { params }),

  /**
   * Get a specific audit log entry
   */
  get: (logId) =>
    client.get(`/api/audit/${logId}`),

  /**
   * Get audit statistics for the past N days
   */
  getStatistics: (days = 7) =>
    client.get('/api/audit/stats/overview', { params: { days } }),

  /**
   * Export audit logs
   */
  export: (format = 'csv', filters = {}, includeDetails = true) =>
    client.post('/api/audit/export', {
      format,
      filters,
      include_details: includeDetails
    }, {
      responseType: 'blob'
    }),

  /**
   * Search audit logs
   */
  search: (searchText, params = {}) =>
    client.get('/api/audit', {
      params: {
        search: searchText,
        ...params
      }
    }),

  /**
   * Get audit logs by user
   */
  getByUser: (userId, params = {}) =>
    client.get('/api/audit', {
      params: {
        user_id: userId,
        ...params
      }
    }),

  /**
   * Get audit logs by action
   */
  getByAction: (action, params = {}) =>
    client.get('/api/audit', {
      params: {
        action,
        ...params
      }
    }),

  /**
   * Get audit logs by resource type
   */
  getByResourceType: (resourceType, params = {}) =>
    client.get('/api/audit', {
      params: {
        resource_type: resourceType,
        ...params
      }
    }),
};

export default auditApi;

