/**
 * Pool Management Page
 * 
 * Create and manage IP pools with advanced options.
 */

import React, { useState } from 'react';
import { FiPlus, FiX, FiCheckCircle, FiAlertCircle, FiEdit, FiTrash2 } from 'react-icons/fi';
import Toast from '../components/Toast';
import apiClient from '../api/client';

const PoolManagement = () => {
  const [showModal, setShowModal] = useState(false);
  const [pools, setPools] = useState([]);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    network: '',
    gateway: '',
    vlan_id: '',
    dns_servers: '',
    description: '',
    template: 'standard'
  });

  const templates = [
    { value: 'standard', label: 'Standard' },
    { value: 'production', label: 'Production' },
    { value: 'test', label: 'Test' },
    { value: 'development', label: 'Development' },
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCreatePool = async () => {
    if (!formData.name || !formData.network) {
      setToast({
        type: 'error',
        message: 'Please fill in required fields (Name, Network)',
        duration: 3000,
      });
      return;
    }

    setLoading(true);
    try {
      const data = {
        name: formData.name,
        network: formData.network,
        gateway: formData.gateway || undefined,
        vlan_id: formData.vlan_id ? parseInt(formData.vlan_id) : undefined,
        dns_servers: formData.dns_servers ? formData.dns_servers.split(',').map(s => s.trim()) : undefined,
        description: formData.description || undefined,
        template: formData.template,
      };

      const response = await apiClient.post('/api/ipam/pools/create-advanced', data);

      setToast({
        type: 'success',
        message: `Pool "${response.data.name}" created successfully`,
        duration: 3000,
      });

      // Reset form
      setFormData({
        name: '',
        network: '',
        gateway: '',
        vlan_id: '',
        dns_servers: '',
        description: '',
        template: 'standard'
      });
      setShowModal(false);

      // Refresh pools list
      await fetchPools();
    } catch (error) {
      setToast({
        type: 'error',
        message: 'Failed to create pool: ' + (error.response?.data?.detail || error.message),
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchPools = async () => {
    try {
      const response = await apiClient.get('/api/ipam/pools');
      setPools(response.data.pools || []);
    } catch (error) {
      console.error('Error fetching pools:', error);
    }
  };

  React.useEffect(() => {
    fetchPools();
  }, []);

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Pool Management</h1>
          <p className="mt-2 text-gray-600">Create and manage IP address pools</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition"
        >
          <FiPlus size={20} />
          Create Pool
        </button>
      </div>

      {/* Pools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {pools.length === 0 ? (
          <div className="col-span-full card text-center py-12">
            <p className="text-gray-500 text-lg">No pools created yet</p>
            <button
              onClick={() => setShowModal(true)}
              className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition"
            >
              Create First Pool
            </button>
          </div>
        ) : (
          pools.map(pool => (
            <div key={pool.id} className="card">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">{pool.name}</h3>
                  <p className="text-sm text-gray-600 font-mono">{pool.network}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => {/* Edit handler */}}
                    className="p-2 hover:bg-gray-100 rounded-lg transition"
                  >
                    <FiEdit size={18} className="text-gray-600" />
                  </button>
                  <button
                    onClick={() => {/* Delete handler */}}
                    className="p-2 hover:bg-red-50 rounded-lg transition"
                  >
                    <FiTrash2 size={18} className="text-red-600" />
                  </button>
                </div>
              </div>

              <div className="space-y-2 text-sm">
                {pool.gateway && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Gateway:</span>
                    <span className="font-mono text-gray-900">{pool.gateway}</span>
                  </div>
                )}
                {pool.vlan_id && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">VLAN:</span>
                    <span className="font-mono text-gray-900">{pool.vlan_id}</span>
                  </div>
                )}
                {pool.template && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Template:</span>
                    <span className="font-mono text-gray-900">{pool.template}</span>
                  </div>
                )}
                {pool.description && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <p className="text-gray-600 text-xs">{pool.description}</p>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Pool Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="flex justify-between items-center p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">Create New Pool</h2>
              <button
                onClick={() => setShowModal(false)}
                className="p-1 hover:bg-gray-100 rounded-lg transition"
              >
                <FiX size={24} className="text-gray-600" />
              </button>
            </div>

            {/* Form */}
            <div className="p-6 space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Pool Name *
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="e.g., Production Pool"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Network */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Network (CIDR) *
                </label>
                <input
                  type="text"
                  name="network"
                  value={formData.network}
                  onChange={handleInputChange}
                  placeholder="e.g., 10.0.0.0/24"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">Must be valid CIDR notation</p>
              </div>

              {/* Gateway */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Gateway IP (Optional)
                </label>
                <input
                  type="text"
                  name="gateway"
                  value={formData.gateway}
                  onChange={handleInputChange}
                  placeholder="e.g., 10.0.0.1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* VLAN */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  VLAN ID (Optional)
                </label>
                <input
                  type="number"
                  name="vlan_id"
                  value={formData.vlan_id}
                  onChange={handleInputChange}
                  placeholder="e.g., 100"
                  min="1"
                  max="4094"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* DNS Servers */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  DNS Servers (Optional)
                </label>
                <input
                  type="text"
                  name="dns_servers"
                  value={formData.dns_servers}
                  onChange={handleInputChange}
                  placeholder="e.g., 8.8.8.8, 8.8.4.4"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">Comma-separated list</p>
              </div>

              {/* Template */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Template
                </label>
                <select
                  name="template"
                  value={formData.template}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {templates.map(t => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description (Optional)
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="Add notes about this pool..."
                  rows="3"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Footer */}
            <div className="flex gap-3 p-6 border-t border-gray-200">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg font-medium transition"
              >
                Cancel
              </button>
              <button
                onClick={handleCreatePool}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition"
              >
                {loading ? 'Creating...' : 'Create Pool'}
              </button>
            </div>
          </div>
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

export default PoolManagement;

