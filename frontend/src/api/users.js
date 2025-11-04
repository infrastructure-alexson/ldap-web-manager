/**
 * User Management API methods
 */

import apiClient from './client';

export const usersApi = {
  /**
   * List all users
   * @param {Object} params - Query parameters (page, page_size, search)
   * @returns {Promise} User list response
   */
  list: async (params = {}) => {
    const response = await apiClient.get('/users', { params });
    return response.data;
  },

  /**
   * Get user by username
   * @param {string} username - Username
   * @returns {Promise} User object
   */
  get: async (username) => {
    const response = await apiClient.get(`/users/${username}`);
    return response.data;
  },

  /**
   * Create new user
   * @param {Object} userData - User data
   * @returns {Promise} Created user
   */
  create: async (userData) => {
    const response = await apiClient.post('/users', userData);
    return response.data;
  },

  /**
   * Update user
   * @param {string} username - Username
   * @param {Object} userData - User data to update
   * @returns {Promise} Updated user
   */
  update: async (username, userData) => {
    const response = await apiClient.patch(`/users/${username}`, userData);
    return response.data;
  },

  /**
   * Delete user
   * @param {string} username - Username
   * @returns {Promise}
   */
  delete: async (username) => {
    const response = await apiClient.delete(`/users/${username}`);
    return response.data;
  },

  /**
   * Reset user password (admin)
   * @param {string} username - Username
   * @param {string} newPassword - New password
   * @returns {Promise}
   */
  resetPassword: async (username, newPassword) => {
    const response = await apiClient.post(`/users/${username}/password`, {
      new_password: newPassword,
    });
    return response.data;
  },
};

