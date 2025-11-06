/**
 * DNS Zone Editor Component
 * 
 * Modal editor for DNS zones with record management
 */

import React, { useState } from 'react';
import { FiX, FiPlus, FiTrash2, FiSave } from 'react-icons/fi';
import Toast from './Toast';
import apiClient from '../api/client';
import { useTheme } from '../contexts/ThemeContext';

const DNSZoneEditor = ({ zone, onClose, onSuccess }) => {
  const { isDarkMode } = useTheme();
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [records, setRecords] = useState(zone?.records || []);
  const [newRecord, setNewRecord] = useState({ name: '', type: 'A', value: '', ttl: 3600 });
  const [formData, setFormData] = useState({
    name: zone?.name || '',
    description: zone?.description || ''
  });

  const recordTypes = ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'SOA', 'SRV', 'TXT'];

  const handleAddRecord = () => {
    if (!newRecord.name || !newRecord.value) {
      setToast({ type: 'error', message: 'Record name and value are required', duration: 3000 });
      return;
    }
    setRecords([...records, { ...newRecord, id: Date.now() }]);
    setNewRecord({ name: '', type: 'A', value: '', ttl: 3600 });
  };

  const handleDeleteRecord = (id) => {
    setRecords(records.filter(r => r.id !== id));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const data = {
        name: formData.name,
        description: formData.description,
        records: records.map(({ id, ...r }) => r)
      };

      if (zone?.id) {
        await apiClient.put(`/api/dns/zones/${zone.id}`, data);
        setToast({ type: 'success', message: 'Zone updated successfully', duration: 3000 });
      } else {
        await apiClient.post('/api/dns/zones', data);
        setToast({ type: 'success', message: 'Zone created successfully', duration: 3000 });
      }

      setTimeout(() => {
        onSuccess?.();
        onClose();
      }, 1500);
    } catch (error) {
      setToast({
        type: 'error',
        message: 'Failed to save zone: ' + (error.response?.data?.detail || error.message),
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className={`card w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-lg shadow-xl ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
        {/* Header */}
        <div className="flex justify-between items-center mb-6 pb-6 border-b sticky top-0" style={{borderColor: isDarkMode ? '#374151' : '#e5e7eb'}}>
          <h2 className={`text-2xl font-bold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
            {zone?.id ? 'Edit DNS Zone' : 'Create DNS Zone'}
          </h2>
          <button onClick={onClose} className={`p-2 rounded-lg transition ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}>
            <FiX className="w-6 h-6" />
          </button>
        </div>

        <div className="space-y-6">
          {/* Zone Info */}
          <div className="space-y-4">
            <h3 className={`font-semibold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>Zone Information</h3>
            
            <div>
              <label className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>Zone Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., example.com"
                className={`w-full px-3 py-2 rounded-lg border transition ${
                  isDarkMode ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-white border-gray-300 text-gray-900'
                } focus:outline-none focus:ring-2 focus:ring-blue-500`}
              />
            </div>

            <div>
              <label className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Add notes about this zone..."
                rows="2"
                className={`w-full px-3 py-2 rounded-lg border transition ${
                  isDarkMode ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-white border-gray-300 text-gray-900'
                } focus:outline-none focus:ring-2 focus:ring-blue-500`}
              />
            </div>
          </div>

          {/* Records */}
          <div className="space-y-4">
            <h3 className={`font-semibold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>DNS Records</h3>

            {/* Add Record */}
            <div className={`p-4 rounded-lg border ${isDarkMode ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'}`}>
              <div className="grid grid-cols-5 gap-3 mb-3">
                <input
                  type="text"
                  placeholder="Name"
                  value={newRecord.name}
                  onChange={(e) => setNewRecord({ ...newRecord, name: e.target.value })}
                  className={`px-3 py-2 rounded border text-sm ${
                    isDarkMode ? 'bg-gray-600 border-gray-500 text-gray-100' : 'bg-white border-gray-300'
                  }`}
                />
                <select
                  value={newRecord.type}
                  onChange={(e) => setNewRecord({ ...newRecord, type: e.target.value })}
                  className={`px-3 py-2 rounded border text-sm ${
                    isDarkMode ? 'bg-gray-600 border-gray-500 text-gray-100' : 'bg-white border-gray-300'
                  }`}
                >
                  {recordTypes.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
                <input
                  type="text"
                  placeholder="Value"
                  value={newRecord.value}
                  onChange={(e) => setNewRecord({ ...newRecord, value: e.target.value })}
                  className={`px-3 py-2 rounded border text-sm ${
                    isDarkMode ? 'bg-gray-600 border-gray-500 text-gray-100' : 'bg-white border-gray-300'
                  }`}
                />
                <input
                  type="number"
                  placeholder="TTL"
                  value={newRecord.ttl}
                  onChange={(e) => setNewRecord({ ...newRecord, ttl: e.target.value })}
                  className={`px-3 py-2 rounded border text-sm ${
                    isDarkMode ? 'bg-gray-600 border-gray-500 text-gray-100' : 'bg-white border-gray-300'
                  }`}
                />
                <button
                  onClick={handleAddRecord}
                  className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded font-medium flex items-center justify-center gap-1"
                >
                  <FiPlus size={16} /> Add
                </button>
              </div>
            </div>

            {/* Records List */}
            {records.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className={`${isDarkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                    <tr>
                      <th className="px-4 py-2 text-left">Name</th>
                      <th className="px-4 py-2 text-left">Type</th>
                      <th className="px-4 py-2 text-left">Value</th>
                      <th className="px-4 py-2 text-left">TTL</th>
                      <th className="px-4 py-2 text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody className={`divide-y ${isDarkMode ? 'divide-gray-700' : 'divide-gray-200'}`}>
                    {records.map(record => (
                      <tr key={record.id} className={isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-50'}>
                        <td className="px-4 py-2">{record.name}</td>
                        <td className="px-4 py-2 font-mono">{record.type}</td>
                        <td className="px-4 py-2 truncate">{record.value}</td>
                        <td className="px-4 py-2">{record.ttl}</td>
                        <td className="px-4 py-2 text-center">
                          <button
                            onClick={() => handleDeleteRecord(record.id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <FiTrash2 size={16} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className={`text-center py-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                No records added yet
              </p>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 pt-6 border-t mt-6" style={{borderColor: isDarkMode ? '#374151' : '#e5e7eb'}}>
          <button
            onClick={onClose}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition ${
              isDarkMode ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition"
          >
            <FiSave size={18} />
            {loading ? 'Saving...' : 'Save Zone'}
          </button>
        </div>

        {toast && <Toast type={toast.type} message={toast.message} duration={toast.duration} onClose={() => setToast(null)} />}
      </div>
    </div>
  );
};

export default DNSZoneEditor;

