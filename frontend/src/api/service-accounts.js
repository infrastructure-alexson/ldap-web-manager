/**
 * Service Accounts API Service
 * 
 * Provides API methods for service account management.
 */

import client from './client';

export const serviceAccountsApi = {
  /**
   * List service accounts
   */
  list: (params = {}) =>
    client.get('/api/service-accounts', { params }),

  /**
   * Get a specific service account
   */
  get: (uid) =>
    client.get(`/api/service-accounts/${uid}`),

  /**
   * Create a new service account
   */
  create: (data) =>
    client.post('/api/service-accounts', data),

  /**
   * Update a service account
   */
  update: (uid, data) =>
    client.patch(`/api/service-accounts/${uid}`, data),

  /**
   * Delete a service account
   */
  delete: (uid) =>
    client.delete(`/api/service-accounts/${uid}`),

  /**
   * Reset service account password
   */
  resetPassword: (uid, password) =>
    client.post(`/api/service-accounts/${uid}/reset-password`, {
      password
    }),
};

export default serviceAccountsApi;

