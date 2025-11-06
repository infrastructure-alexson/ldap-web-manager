/**
 * Subnet Calculator Page
 * 
 * Advanced subnet calculations, splitting, and merging.
 */

import React, { useState } from 'react';
import { FiCalculator, FiCopy, FiCheck } from 'react-icons/fi';
import Toast from '../components/Toast';
import apiClient from '../api/client';

const SubnetCalculator = () => {
  const [operation, setOperation] = useState('info');
  const [network, setNetwork] = useState('');
  const [networks, setNetworks] = useState('');
  const [subnetCount, setSubnetCount] = useState(2);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [copiedIndex, setCopiedIndex] = useState(null);

  const operations = [
    { value: 'info', label: 'Subnet Information', icon: 'ℹ️' },
    { value: 'split', label: 'Split Network', icon: '✂️' },
    { value: 'merge', label: 'Merge Networks', icon: '🔗' },
    { value: 'validate', label: 'Validate Network', icon: '✓' },
  ];

  const handleCalculate = async () => {
    if ((operation === 'split' || operation === 'info' || operation === 'validate') && !network.trim()) {
      setToast({
        type: 'error',
        message: 'Please enter a network address',
        duration: 3000,
      });
      return;
    }

    if (operation === 'merge' && !networks.trim()) {
      setToast({
        type: 'error',
        message: 'Please enter networks to merge',
        duration: 3000,
      });
      return;
    }

    setLoading(true);
    try {
      let data = { operation };

      if (operation === 'split' || operation === 'info' || operation === 'validate') {
        data.network = network.trim();
        if (operation === 'split') {
          data.subnet_count = parseInt(subnetCount);
        }
      } else if (operation === 'merge') {
        data.networks = networks.trim().split('\n').filter(n => n.trim());
      }

      const response = await apiClient.post('/api/ipam/calculator', data);
      setResult(response.data);

      setToast({
        type: 'success',
        message: 'Calculation completed',
        duration: 3000,
      });
    } catch (error) {
      setToast({
        type: 'error',
        message: 'Calculation failed: ' + (error.response?.data?.detail || error.message),
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text, index) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);

    setToast({
      type: 'success',
      message: 'Copied to clipboard',
      duration: 2000,
    });
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Subnet Calculator</h1>
        <p className="mt-2 text-gray-600">
          Calculate network information, split networks, merge subnets, and validate addresses
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calculator Panel */}
        <div className="lg:col-span-1">
          <div className="card sticky top-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Calculator</h2>

            {/* Operation Selection */}
            <div className="space-y-3 mb-6">
              {operations.map(op => (
                <button
                  key={op.value}
                  onClick={() => {
                    setOperation(op.value);
                    setResult(null);
                  }}
                  className={`w-full text-left px-4 py-3 rounded-lg font-medium transition ${
                    operation === op.value
                      ? 'bg-blue-100 text-blue-900 border-2 border-blue-500'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border-2 border-transparent'
                  }`}
                >
                  <span className="mr-2">{op.icon}</span>
                  {op.label}
                </button>
              ))}
            </div>

            {/* Input Fields */}
            <div className="space-y-4">
              {(operation === 'split' || operation === 'info' || operation === 'validate') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Network Address
                  </label>
                  <input
                    type="text"
                    value={network}
                    onChange={(e) => setNetwork(e.target.value)}
                    placeholder="e.g., 10.0.0.0/24"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}

              {operation === 'split' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Number of Subnets
                  </label>
                  <select
                    value={subnetCount}
                    onChange={(e) => setSubnetCount(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {[2, 4, 8, 16, 32, 64, 128, 256].map(num => (
                      <option key={num} value={num}>{num} Subnets</option>
                    ))}
                  </select>
                </div>
              )}

              {operation === 'merge' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Networks to Merge
                  </label>
                  <textarea
                    value={networks}
                    onChange={(e) => setNetworks(e.target.value)}
                    placeholder="Enter one network per line&#10;e.g., 10.0.0.0/25&#10;     10.0.0.128/25"
                    rows="5"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}

              <button
                onClick={handleCalculate}
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition"
              >
                <FiCalculator size={18} />
                {loading ? 'Calculating...' : 'Calculate'}
              </button>
            </div>
          </div>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-2">
          {result ? (
            <div className="card">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Results</h2>

              {operation === 'info' && result.prefix_length !== undefined && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">Network Address</p>
                      <p className="text-lg font-mono text-gray-900 mt-1">{result.network}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">Netmask</p>
                      <p className="text-lg font-mono text-gray-900 mt-1">{result.netmask}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">CIDR Prefix</p>
                      <p className="text-lg font-mono text-gray-900 mt-1">/{result.prefix_length}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">Broadcast</p>
                      <p className="text-lg font-mono text-gray-900 mt-1">{result.broadcast}</p>
                    </div>
                    <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
                      <p className="text-sm text-gray-600">First Host</p>
                      <p className="text-lg font-mono text-blue-900 mt-1">{result.first_host}</p>
                    </div>
                    <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
                      <p className="text-sm text-gray-600">Last Host</p>
                      <p className="text-lg font-mono text-blue-900 mt-1">{result.last_host}</p>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg border-l-4 border-green-500">
                      <p className="text-sm text-gray-600">Total Hosts</p>
                      <p className="text-lg font-bold text-green-900 mt-1">{result.total_hosts}</p>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg border-l-4 border-green-500">
                      <p className="text-sm text-gray-600">Usable Hosts</p>
                      <p className="text-lg font-bold text-green-900 mt-1">{result.usable_hosts}</p>
                    </div>
                  </div>
                </div>
              )}

              {operation === 'split' && result.subnets && (
                <div>
                  <p className="text-gray-600 mb-4">
                    Original network split into {result.subnet_count} subnets with {result.hosts_per_subnet} usable hosts each
                  </p>
                  <div className="space-y-2">
                    {result.subnets.map((subnet, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
                        <span className="font-mono text-gray-900">{subnet}</span>
                        <button
                          onClick={() => copyToClipboard(subnet, idx)}
                          className={`p-2 rounded transition ${
                            copiedIndex === idx ? 'bg-green-100' : 'hover:bg-gray-200'
                          }`}
                        >
                          {copiedIndex === idx ? (
                            <FiCheck size={18} className="text-green-600" />
                          ) : (
                            <FiCopy size={18} className="text-gray-600" />
                          )}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {operation === 'merge' && result.merged_network && (
                <div className="space-y-4">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-600">Merged Network</p>
                    <p className="text-2xl font-mono text-gray-900 mt-2">{result.merged_network}</p>
                  </div>
                  <p className="text-gray-600 text-sm">
                    Successfully merged {result.subnets.length} network(s)
                  </p>
                </div>
              )}

              {operation === 'validate' && result.valid !== undefined && (
                <div className={`p-4 rounded-lg ${result.valid ? 'bg-green-50 border-2 border-green-300' : 'bg-red-50 border-2 border-red-300'}`}>
                  <p className={`text-lg font-bold ${result.valid ? 'text-green-900' : 'text-red-900'}`}>
                    {result.valid ? '✓ Valid Network' : '✗ Invalid Network'}
                  </p>
                  <p className={`text-sm mt-2 ${result.valid ? 'text-green-700' : 'text-red-700'}`}>
                    {result.message}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="card text-center py-12">
              <FiCalculator size={48} className="mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500 text-lg">Select an operation and click Calculate</p>
            </div>
          )}
        </div>
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
  );
};

export default SubnetCalculator;

