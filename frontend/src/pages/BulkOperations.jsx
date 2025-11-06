/**
 * Bulk Operations Page
 * 
 * Perform bulk operations on users, groups, DNS, and IPAM resources.
 */

import React, { useState } from 'react';
import { FiUpload, FiPlayCircle, FiCheckCircle, FiAlertCircle, FiX, FiDownload } from 'react-icons/fi';
import Toast from '../components/Toast';
import apiClient from '../api/client';

const BulkOperations = () => {
  const [operationType, setOperationType] = useState('users'); // users, groups, dns, ipam
  const [operation, setOperation] = useState('create'); // create, update, delete, add_to_group
  const [csvFile, setCsvFile] = useState(null);
  const [manualEntries, setManualEntries] = useState('');
  const [useCSV, setUseCSV] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState(null);
  const [toast, setToast] = useState(null);

  const operationOptions = {
    users: [
      { value: 'create', label: 'Create Users' },
      { value: 'update', label: 'Update Users' },
      { value: 'delete', label: 'Delete Users' },
    ],
    groups: [
      { value: 'add_to_group', label: 'Add to Group' },
      { value: 'remove_from_group', label: 'Remove from Group' },
    ],
    dns: [
      { value: 'create', label: 'Create Records' },
      { value: 'update', label: 'Update Records' },
      { value: 'delete', label: 'Delete Records' },
    ],
    ipam: [
      { value: 'allocate', label: 'Allocate IPs' },
      { value: 'release', label: 'Release IPs' },
      { value: 'update', label: 'Update IPs' },
    ],
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
        setToast({
          type: 'error',
          message: 'Please upload a CSV file',
          duration: 3000,
        });
        return;
      }
      setCsvFile(file);
    }
  };

  const handleExecute = async () => {
    if (!useCSV && !manualEntries.trim()) {
      setToast({
        type: 'error',
        message: 'Please enter data or upload a CSV file',
        duration: 3000,
      });
      return;
    }

    setIsProcessing(true);
    try {
      let data;

      if (useCSV && csvFile) {
        // Parse CSV file
        const text = await csvFile.text();
        const lines = text.trim().split('\n');
        const headers = lines[0].split(',').map(h => h.trim());
        
        // Parse data based on operation type
        const rows = lines.slice(1).map(line => {
          const values = line.split(',').map(v => v.trim());
          const row = {};
          headers.forEach((header, idx) => {
            row[header] = values[idx] || '';
          });
          return row;
        });

        // Build request based on operation type
        if (operationType === 'users') {
          data = {
            operation: operation.toUpperCase(),
            usernames: rows.map(r => r.username || r.uid),
            common_name: rows[0]?.common_name,
            mail: rows[0]?.mail,
          };
        } else if (operationType === 'groups') {
          data = {
            operation: operation.toUpperCase(),
            group_name: rows[0]?.group_name,
            usernames: rows.map(r => r.username || r.uid),
          };
        } else if (operationType === 'dns') {
          data = {
            operation,
            zone_name: rows[0]?.zone_name,
            records: rows.map(r => ({
              name: r.name,
              type: r.type,
              value: r.value,
              ttl: parseInt(r.ttl) || 3600,
            })),
          };
        } else if (operationType === 'ipam') {
          data = {
            operation,
            pool_id: parseInt(rows[0]?.pool_id),
            allocations: rows.map(r => ({
              ip_address: r.ip_address,
              hostname: r.hostname,
              mac_address: r.mac_address,
              owner: r.owner,
              purpose: r.purpose,
            })),
          };
        }
      } else {
        // Parse manual entries (one per line)
        const entries = manualEntries.trim().split('\n').filter(e => e.trim());

        if (operationType === 'users') {
          data = {
            operation: operation.toUpperCase(),
            usernames: entries,
          };
        } else if (operationType === 'groups') {
          const [groupName, ...usernames] = entries;
          data = {
            operation: operation.toUpperCase(),
            group_name: groupName,
            usernames,
          };
        } else if (operationType === 'dns') {
          data = {
            operation,
            zone_name: entries[0],
            records: entries.slice(1).map(entry => {
              const [name, type, value, ttl] = entry.split('\t');
              return { name, type, value, ttl: parseInt(ttl) || 3600 };
            }),
          };
        } else if (operationType === 'ipam') {
          data = {
            operation,
            pool_id: parseInt(entries[0]),
            allocations: entries.slice(1).map(entry => {
              const [ip, hostname, mac, owner, purpose] = entry.split('\t');
              return { ip_address: ip, hostname, mac_address: mac, owner, purpose };
            }),
          };
        }
      }

      // Call API
      const response = await apiClient.post(`/api/bulk/${operationType}`, data);

      setResults(response.data);
      setToast({
        type: 'success',
        message: `Bulk operation completed: ${response.data.successful} successful, ${response.data.failed} failed`,
        duration: 5000,
      });
    } catch (error) {
      setToast({
        type: 'error',
        message: 'Bulk operation failed: ' + (error.response?.data?.detail || error.message),
        duration: 5000,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const downloadTemplate = () => {
    let csv = '';

    if (operationType === 'users') {
      csv = 'username,common_name,mail,description\nuser1,User One,user1@example.com,Description\nuser2,User Two,user2@example.com,Description';
    } else if (operationType === 'groups') {
      csv = 'group_name,username\ndevelopers,user1\ndevelopers,user2\ndevelopers,user3';
    } else if (operationType === 'dns') {
      csv = 'zone_name,name,type,value,ttl\nexample.com,www,A,192.168.1.100,3600\nexample.com,mail,A,192.168.1.101,3600';
    } else if (operationType === 'ipam') {
      csv = 'pool_id,ip_address,hostname,mac_address,owner,purpose\n1,10.0.0.50,server1,00:11:22:33:44:55,admin,server\n1,10.0.0.51,server2,00:11:22:33:44:56,admin,server';
    }

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bulk_${operationType}_template.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Bulk Operations</h1>
        <p className="mt-2 text-gray-600">
          Perform batch operations on users, groups, DNS records, and IP allocations
        </p>
      </div>

      {/* Configuration */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Operation Type */}
        <div className="card">
          <label className="block text-sm font-medium text-gray-700 mb-2">Resource Type</label>
          <select
            value={operationType}
            onChange={(e) => {
              setOperationType(e.target.value);
              setOperation(operationOptions[e.target.value]?.[0]?.value || '');
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="users">Users</option>
            <option value="groups">Groups</option>
            <option value="dns">DNS Records</option>
            <option value="ipam">IP Allocations</option>
          </select>
        </div>

        {/* Operation */}
        <div className="card">
          <label className="block text-sm font-medium text-gray-700 mb-2">Operation</label>
          <select
            value={operation}
            onChange={(e) => setOperation(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {operationOptions[operationType]?.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Input Method */}
      <div className="card mb-6">
        <div className="flex gap-4 mb-4">
          <label className="flex items-center">
            <input
              type="radio"
              checked={!useCSV}
              onChange={() => setUseCSV(false)}
              className="mr-2"
            />
            <span className="text-sm font-medium text-gray-700">Manual Entry</span>
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              checked={useCSV}
              onChange={() => setUseCSV(true)}
              className="mr-2"
            />
            <span className="text-sm font-medium text-gray-700">CSV Upload</span>
          </label>
        </div>

        {useCSV ? (
          <div>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <FiUpload className="mx-auto h-8 w-8 text-gray-400 mb-2" />
              <label className="cursor-pointer">
                <span className="text-blue-600 hover:text-blue-700">Click to upload</span>
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
              <p className="text-xs text-gray-500 mt-2">or drag and drop</p>
              {csvFile && (
                <p className="text-sm text-green-600 mt-2 flex items-center justify-center gap-2">
                  <FiCheckCircle size={16} />
                  {csvFile.name}
                </p>
              )}
            </div>
            <button
              onClick={downloadTemplate}
              className="mt-3 flex items-center gap-2 text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              <FiDownload size={16} />
              Download Template
            </button>
          </div>
        ) : (
          <div>
            <textarea
              value={manualEntries}
              onChange={(e) => setManualEntries(e.target.value)}
              placeholder="Enter one item per line. For groups: group_name on first line, then usernames."
              className="w-full h-40 px-3 py-2 border border-gray-300 rounded-md font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-2">
              Format depends on resource type. See hints in placeholder text.
            </p>
          </div>
        )}
      </div>

      {/* Execute Button */}
      <div className="mb-6">
        <button
          onClick={handleExecute}
          disabled={isProcessing || (useCSV ? !csvFile : !manualEntries.trim())}
          className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition"
        >
          <FiPlayCircle size={20} />
          {isProcessing ? 'Processing...' : 'Execute Bulk Operation'}
        </button>
      </div>

      {/* Results */}
      {results && (
        <div className="card">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Results</h2>

            {/* Summary */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Total</p>
                <p className="text-2xl font-bold text-gray-900">{results.total}</p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Successful</p>
                <p className="text-2xl font-bold text-green-600">{results.successful}</p>
              </div>
              <div className="bg-red-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Failed</p>
                <p className="text-2xl font-bold text-red-600">{results.failed}</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Skipped</p>
                <p className="text-2xl font-bold text-gray-600">{results.skipped}</p>
              </div>
            </div>

            {/* Summary Message */}
            <p className="text-lg font-medium text-gray-900 mb-6">{results.summary}</p>

            {/* Details Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left font-semibold text-gray-900">#</th>
                    <th className="px-4 py-2 text-left font-semibold text-gray-900">Identifier</th>
                    <th className="px-4 py-2 text-left font-semibold text-gray-900">Status</th>
                    <th className="px-4 py-2 text-left font-semibold text-gray-900">Message</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {results.results.map((result, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-4 py-2 text-gray-600">{result.index + 1}</td>
                      <td className="px-4 py-2 font-mono text-gray-900">{result.identifier}</td>
                      <td className="px-4 py-2">
                        <div className="flex items-center gap-2">
                          {result.status === 'success' && (
                            <>
                              <FiCheckCircle className="text-green-600" size={16} />
                              <span className="text-green-600 font-medium">Success</span>
                            </>
                          )}
                          {result.status === 'failure' && (
                            <>
                              <FiAlertCircle className="text-red-600" size={16} />
                              <span className="text-red-600 font-medium">Failed</span>
                            </>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-2 text-gray-600">{result.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <button
            onClick={() => setResults(null)}
            className="text-gray-600 hover:text-gray-900 text-sm font-medium flex items-center gap-2"
          >
            <FiX size={16} />
            Clear Results
          </button>
        </div>
      )}

      {/* Toast Notification */}
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

export default BulkOperations;

