import React, { useState } from 'react';
import { FiX } from 'react-icons/fi';

/**
 * AllocationModal Component
 * 
 * Modal form for allocating an IP address with hostname, MAC, owner, and purpose.
 */
const AllocationModal = ({ ip, onConfirm, onCancel }) => {
  const [formData, setFormData] = useState({
    hostname: '',
    mac_address: '',
    owner: '',
    purpose: '',
    description: '',
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Validate MAC address format
  const validateMAC = (mac) => {
    if (!mac) return true; // Optional field
    const macRegex = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/;
    return macRegex.test(mac);
  };

  // Validate hostname format
  const validateHostname = (hostname) => {
    if (!hostname) return true; // Optional field
    const hostnameRegex = /^([a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\.)*([a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)$/;
    return hostnameRegex.test(hostname);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate
    const newErrors = {};
    
    if (!formData.owner.trim()) {
      newErrors.owner = 'Owner is required';
    }
    
    if (formData.hostname && !validateHostname(formData.hostname)) {
      newErrors.hostname = 'Invalid hostname format';
    }
    
    if (formData.mac_address && !validateMAC(formData.mac_address)) {
      newErrors.mac_address = 'Invalid MAC address format (XX:XX:XX:XX:XX:XX)';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsSubmitting(true);
    try {
      await onConfirm({
        hostname: formData.hostname || null,
        mac_address: formData.mac_address || null,
        owner: formData.owner,
        purpose: formData.purpose || null,
        description: formData.description || null,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-md w-full max-h-screen overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Allocate IP Address</h2>
          <button
            onClick={onCancel}
            className="p-1 hover:bg-gray-100 rounded transition"
          >
            <FiX size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* IP Address Display */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              IP Address
            </label>
            <div className="px-3 py-2 bg-gray-100 border border-gray-300 rounded-lg font-mono font-bold text-gray-900">
              {ip.ip_address}
            </div>
          </div>

          {/* Owner (Required) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Owner <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="owner"
              value={formData.owner}
              onChange={handleChange}
              placeholder="User or service name"
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.owner ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.owner && (
              <p className="mt-1 text-sm text-red-600">{errors.owner}</p>
            )}
          </div>

          {/* Hostname (Optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Hostname <span className="text-gray-500 text-xs">(optional)</span>
            </label>
            <input
              type="text"
              name="hostname"
              value={formData.hostname}
              onChange={handleChange}
              placeholder="e.g., server.example.com"
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.hostname ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.hostname && (
              <p className="mt-1 text-sm text-red-600">{errors.hostname}</p>
            )}
          </div>

          {/* MAC Address (Optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              MAC Address <span className="text-gray-500 text-xs">(optional)</span>
            </label>
            <input
              type="text"
              name="mac_address"
              value={formData.mac_address}
              onChange={handleChange}
              placeholder="e.g., 00:11:22:33:44:55"
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.mac_address ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.mac_address && (
              <p className="mt-1 text-sm text-red-600">{errors.mac_address}</p>
            )}
          </div>

          {/* Purpose (Optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Purpose <span className="text-gray-500 text-xs">(optional)</span>
            </label>
            <select
              name="purpose"
              value={formData.purpose}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">-- Select Purpose --</option>
              <option value="server">Server</option>
              <option value="workstation">Workstation</option>
              <option value="printer">Printer</option>
              <option value="network-device">Network Device</option>
              <option value="service">Service</option>
              <option value="other">Other</option>
            </select>
          </div>

          {/* Description (Optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description <span className="text-gray-500 text-xs">(optional)</span>
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Additional notes or context..."
              rows="3"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onCancel}
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-400 text-white rounded-lg transition"
            >
              {isSubmitting ? 'Allocating...' : 'Allocate IP'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AllocationModal;


