/**
 * Group Management API methods
 */

import apiClient from './client';

export const groupsApi = {
  /**
   * List all groups
   * @param {Object} params - Query parameters (page, page_size, search)
   * @returns {Promise} Group list response
   */
  list: async (params = {}) => {
    const response = await apiClient.get('/groups', { params });
    return response.data;
  },

  /**
   * Get group by name
   * @param {string} groupName - Group name
   * @returns {Promise} Group object
   */
  get: async (groupName) => {
    const response = await apiClient.get(`/groups/${groupName}`);
    return response.data;
  },

  /**
   * Create new group
   * @param {Object} groupData - Group data
   * @returns {Promise} Created group
   */
  create: async (groupData) => {
    const response = await apiClient.post('/groups', groupData);
    return response.data;
  },

  /**
   * Update group
   * @param {string} groupName - Group name
   * @param {Object} groupData - Group data to update
   * @returns {Promise} Updated group
   */
  update: async (groupName, groupData) => {
    const response = await apiClient.patch(`/groups/${groupName}`, groupData);
    return response.data;
  },

  /**
   * Delete group
   * @param {string} groupName - Group name
   * @returns {Promise}
   */
  delete: async (groupName) => {
    const response = await apiClient.delete(`/groups/${groupName}`);
    return response.data;
  },

  /**
   * Add member to group
   * @param {string} groupName - Group name
   * @param {string} username - Username to add
   * @returns {Promise} Updated group
   */
  addMember: async (groupName, username) => {
    const response = await apiClient.post(`/groups/${groupName}/members`, {
      username,
    });
    return response.data;
  },

  /**
   * Remove member from group
   * @param {string} groupName - Group name
   * @param {string} username - Username to remove
   * @returns {Promise} Updated group
   */
  removeMember: async (groupName, username) => {
    const response = await apiClient.delete(`/groups/${groupName}/members/${username}`);
    return response.data;
  },
};

