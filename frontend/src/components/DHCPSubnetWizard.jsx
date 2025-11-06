/**
 * DHCP Subnet Wizard Component
 * 
 * Step-by-step wizard for creating DHCP subnets
 */

import React, { useState } from 'react';
import { FiChevronRight, FiChevronLeft, FiCheck, FiX } from 'react-icons/fi';
import Toast from './Toast';
import apiClient from '../api/client';
import { useTheme } from '../contexts/ThemeContext';

const DHCPSubnetWizard = ({ onClose, onSuccess }) => {
  const { isDarkMode } = useTheme();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);

  const [formData, setFormData] = useState({
    // Step 1: Basic Info
    name: '',
    network: '',
    
    // Step 2: Gateway & Range
    gateway: '',
    range_start: '',
    range_end: '',
    
    // Step 3: DNS & NTP
    dns_servers: '',
    ntp_servers: '',
    
    // Step 4: Advanced
    lease_time: 3600,
    renewal_time: 1800,
    rebind_time: 3150,
    description: ''
  });

  const [errors, setErrors] = useState({});

  const validateStep = (currentStep) => {
    const newErrors = {};

    if (currentStep === 1) {
      if (!formData.name.trim()) newErrors.name = 'Subnet name is required';
      if (!formData.network.trim()) newErrors.network = 'Network is required';
    } else if (currentStep === 2) {
      if (!formData.gateway.trim()) newErrors.gateway = 'Gateway is required';
      if (!formData.range_start.trim()) newErrors.range_start = 'Range start is required';
      if (!formData.range_end.trim()) newErrors.range_end = 'Range end is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handleNext = () => {
    if (validateStep(step)) {
      setStep(step + 1);
    }
  };

  const handlePrev = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const handleCreate = async () => {
    if (!validateStep(step)) {
      return;
    }

    setLoading(true);
    try {
      const data = {
        name: formData.name,
        network: formData.network,
        gateway: formData.gateway,
        range_start: formData.range_start,
        range_end: formData.range_end,
        dns_servers: formData.dns_servers ? formData.dns_servers.split(',').map(s => s.trim()) : undefined,
        ntp_servers: formData.ntp_servers ? formData.ntp_servers.split(',').map(s => s.trim()) : undefined,
        lease_time: parseInt(formData.lease_time),
        renewal_time: parseInt(formData.renewal_time),
        rebind_time: parseInt(formData.rebind_time),
        description: formData.description || undefined
      };

      await apiClient.post('/api/dhcp/subnets', data);

      setToast({
        type: 'success',
        message: `Subnet "${formData.name}" created successfully!`,
        duration: 3000,
      });

      setTimeout(() => {
        onSuccess?.();
        onClose();
      }, 1500);
    } catch (error) {
      setToast({
        type: 'error',
        message: 'Failed to create subnet: ' + (error.response?.data?.detail || error.message),
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  };

  const getCardClass = () => `
    card sticky top-20 p-6 ${isDarkMode ? 'bg-gray-800' : 'bg-white'}
  `;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className={`${getCardClass()} w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-lg shadow-xl`}>
        {/* Header */}
        <div className="flex justify-between items-center mb-6 pb-6 border-b" style={{borderColor: isDarkMode ? '#374151' : '#e5e7eb'}}>
          <div>
            <h2 className={`text-2xl font-bold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
              DHCP Subnet Wizard
            </h2>
            <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Step {step} of 4
            </p>
          </div>
          <button
            onClick={onClose}
            className={`p-2 rounded-lg transition ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
          >
            <FiX className="w-6 h-6" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="flex gap-2 mb-8">
          {[1, 2, 3, 4].map(s => (
            <div
              key={s}
              className={`h-2 flex-1 rounded-full transition ${
                s <= step
                  ? 'bg-blue-500'
                  : isDarkMode ? 'bg-gray-700' : 'bg-gray-200'
              }`}
            />
          ))}
        </div>

        {/* Step Content */}
        <div className="mb-8">
          {/* Step 1: Basic Info */}
          {step === 1 && (
            <div className="space-y-4">
              <h3 className={`text-lg font-semibold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                Basic Information
              </h3>
              
              <div>
                <label className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Subnet Name *
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="e.g., Office Network"
                  className={`w-full px-3 py-2 rounded-lg border transition ${
                    isDarkMode
                      ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500'
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                  } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                />
                {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
              </div>

              <div>
                <label className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Network (CIDR) *
                </label>
                <input
                  type="text"
                  name="network"
                  value={formData.network}
                  onChange={handleInputChange}
                  placeholder="e.g., 192.168.1.0/24"
                  className={`w-full px-3 py-2 rounded-lg border transition ${
                    isDarkMode
                      ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500'
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                  } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                />
                {errors.network && <p className="text-red-500 text-sm mt-1">{errors.network}</p>}
              </div>
            </div>
          )}

          {/* Step 2: Gateway & Range */}
          {step === 2 && (
            <div className="space-y-4">
              <h3 className={`text-lg font-semibold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                Gateway & IP Range
              </h3>

              <div>
                <label className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Gateway IP *
                </label>
                <input
                  type="text"
                  name="gateway"
                  value={formData.gateway}
                  onChange={handleInputChange}
                  placeholder="e.g., 192.168.1.1"
                  className={`w-full px-3 py-2 rounded-lg border transition ${
                    isDarkMode
                      ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500'
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                  } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                />
                {errors.gateway && <p className="text-red-500 text-sm mt-1">{errors.gateway}</p>}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                    Range Start *
                  </label>
                  <input
                    type="text"
                    name="range_start"
                    value={formData.range_start}
                    onChange={handleInputChange}
                    placeholder="e.g., 192.168.1.100"
                    className={`w-full px-3 py-2 rounded-lg border transition ${
                      isDarkMode
                        ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500'
                        : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                    } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  />
                  {errors.range_start && <p className="text-red-500 text-sm mt-1">{errors.range_start}</p>}
                </div>

                <div>
                  <label className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                    Range End *
                  </label>
                  <input
                    type="text"
                    name="range_end"
                    value={formData.range_end}
                    onChange={handleInputChange}
                    placeholder="e.g., 192.168.1.254"
                    className={`w-full px-3 py-2 rounded-lg border transition ${
                      isDarkMode
                        ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500'
                        : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                    } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  />
                  {errors.range_end && <p className="text-red-500 text-sm mt-1">{errors.range_end}</p>}
                </div>
              </div>
            </div>
          )}

          {/* Step 3: DNS & NTP */}
          {step === 3 && (
            <div className="space-y-4">
              <h3 className={`text-lg font-semibold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                DNS & NTP Servers
              </h3>

              <div>
                <label className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  DNS Servers (Optional)
                </label>
                <input
                  type="text"
                  name="dns_servers"
                  value={formData.dns_servers}
                  onChange={handleInputChange}
                  placeholder="e.g., 8.8.8.8, 8.8.4.4"
                  className={`w-full px-3 py-2 rounded-lg border transition ${
                    isDarkMode
                      ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500'
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                  } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                />
                <p className={`text-xs mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  Comma-separated list of DNS servers
                </p>
              </div>

              <div>
                <label className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  NTP Servers (Optional)
                </label>
                <input
                  type="text"
                  name="ntp_servers"
                  value={formData.ntp_servers}
                  onChange={handleInputChange}
                  placeholder="e.g., 0.pool.ntp.org, 1.pool.ntp.org"
                  className={`w-full px-3 py-2 rounded-lg border transition ${
                    isDarkMode
                      ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500'
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                  } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                />
                <p className={`text-xs mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  Comma-separated list of NTP servers
                </p>
              </div>
            </div>
          )}

          {/* Step 4: Advanced */}
          {step === 4 && (
            <div className="space-y-4">
              <h3 className={`text-lg font-semibold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                Advanced Settings
              </h3>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                    Lease Time (s)
                  </label>
                  <input
                    type="number"
                    name="lease_time"
                    value={formData.lease_time}
                    onChange={handleInputChange}
                    min="300"
                    className={`w-full px-3 py-2 rounded-lg border transition ${
                      isDarkMode
                        ? 'bg-gray-700 border-gray-600 text-gray-100'
                        : 'bg-white border-gray-300 text-gray-900'
                    } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  />
                </div>

                <div>
                  <label className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                    Renewal Time (s)
                  </label>
                  <input
                    type="number"
                    name="renewal_time"
                    value={formData.renewal_time}
                    onChange={handleInputChange}
                    min="60"
                    className={`w-full px-3 py-2 rounded-lg border transition ${
                      isDarkMode
                        ? 'bg-gray-700 border-gray-600 text-gray-100'
                        : 'bg-white border-gray-300 text-gray-900'
                    } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  />
                </div>

                <div>
                  <label className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                    Rebind Time (s)
                  </label>
                  <input
                    type="number"
                    name="rebind_time"
                    value={formData.rebind_time}
                    onChange={handleInputChange}
                    min="60"
                    className={`w-full px-3 py-2 rounded-lg border transition ${
                      isDarkMode
                        ? 'bg-gray-700 border-gray-600 text-gray-100'
                        : 'bg-white border-gray-300 text-gray-900'
                    } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  />
                </div>
              </div>

              <div>
                <label className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Description (Optional)
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="Add notes about this subnet..."
                  rows="3"
                  className={`w-full px-3 py-2 rounded-lg border transition ${
                    isDarkMode
                      ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500'
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                  } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                />
              </div>
            </div>
          )}
        </div>

        {/* Navigation Buttons */}
        <div className="flex gap-3">
          <button
            onClick={handlePrev}
            disabled={step === 1}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition disabled:opacity-50 ${
              isDarkMode
                ? 'bg-gray-700 text-gray-300 hover:bg-gray-600 disabled:hover:bg-gray-700'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300 disabled:hover:bg-gray-200'
            }`}
          >
            <FiChevronLeft size={18} />
            Previous
          </button>

          {step < 4 ? (
            <button
              onClick={handleNext}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition"
            >
              Next
              <FiChevronRight size={18} />
            </button>
          ) : (
            <button
              onClick={handleCreate}
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition"
            >
              <FiCheck size={18} />
              {loading ? 'Creating...' : 'Create Subnet'}
            </button>
          )}
        </div>

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
    </div>
  );
};

export default DHCPSubnetWizard;

