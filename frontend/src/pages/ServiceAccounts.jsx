/**
 * Service Accounts Management Page
 * 
 * Displays and manages service accounts for system integrations.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { serviceAccountsApi } from '../api/service-accounts';
import { FiPlus, FiSearch, FiEdit, FiTrash2, FiKey, FiServer } from 'react-icons/fi';
import Toast from '../components/Toast';

const ServiceAccounts = () => {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);
  const [toast, setToast] = useState(null);
  const queryClient = useQueryClient();

  // Fetch service accounts
  const { data, isLoading, error } = useQuery({
    queryKey: ['service-accounts', page, search],
    queryFn: () => serviceAccountsApi.list({ page, page_size: 20, search: search || undefined }),
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (accountData) => serviceAccountsApi.create(accountData),
    onSuccess: () => {
      queryClient.invalidateQueries(['service-accounts']);
      setShowCreateModal(false);
      setToast({
        type: 'success',
        message: 'Service account created successfully',
        duration: 3000,
      });
    },
    onError: (error) => {
      setToast({
        type: 'error',
        message: 'Failed to create service account: ' + (error.response?.data?.detail || error.message),
        duration: 5000,
      });
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (uid) => serviceAccountsApi.delete(uid),
    onSuccess: () => {
      queryClient.invalidateQueries(['service-accounts']);
      setToast({
        type: 'success',
        message: 'Service account deleted successfully',
        duration: 3000,
      });
    },
    onError: (error) => {
      setToast({
        type: 'error',
        message: 'Failed to delete service account: ' + (error.response?.data?.detail || error.message),
        duration: 5000,
      });
    },
  });

  // Reset password mutation
  const resetPasswordMutation = useMutation({
    mutationFn: ({ uid, password }) => serviceAccountsApi.resetPassword(uid, password),
    onSuccess: () => {
      queryClient.invalidateQueries(['service-accounts']);
      setToast({
        type: 'success',
        message: 'Password reset successfully',
        duration: 3000,
      });
    },
    onError: (error) => {
      setToast({
        type: 'error',
        message: 'Failed to reset password: ' + (error.response?.data?.detail || error.message),
        duration: 5000,
      });
    },
  });

  const handleDelete = (uid) => {
    if (window.confirm(`Are you sure you want to delete service account ${uid}?`)) {
      deleteMutation.mutate(uid);
    }
  };

  const handleSearch = (e) => {
    setSearch(e.target.value);
    setPage(1);
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Service Accounts</h1>
          <p className="mt-2 text-gray-600">
            Manage service accounts for system integrations (DHCP, DNS, etc.)
          </p>
        </div>
        <button 
          onClick={() => setShowCreateModal(true)}
          className="btn-primary flex items-center"
        >
          <FiPlus className="mr-2" />
          Create Account
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 text-sm">{error.message || 'Failed to load service accounts'}</p>
        </div>
      )}

      {/* Search */}
      <div className="mb-6 card">
        <div className="relative">
          <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search service accounts..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={search}
            onChange={handleSearch}
          />
        </div>
      </div>

      {/* Service Accounts Table */}
      {isLoading ? (
        <div className="card text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading service accounts...</p>
        </div>
      ) : data?.items?.length === 0 ? (
        <div className="card text-center py-12">
          <FiServer className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-4 text-gray-600">No service accounts found</p>
          <p className="text-sm text-gray-500">Create a new service account to get started</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                  Account
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                  Created
                </th>
                <th className="px-6 py-3 text-right text-sm font-semibold text-gray-900">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {data?.items?.map((account) => (
                <tr key={account.uid} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <FiServer className="text-blue-500 mr-2" />
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {account.cn}
                        </div>
                        <div className="text-xs text-gray-500 font-mono">
                          {account.uid}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-600">
                      {account.mail || '—'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm text-gray-600 max-w-xs truncate block">
                      {account.description || '—'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      account.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {account.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-600">
                      {account.created_at ? new Date(account.created_at).toLocaleDateString() : '—'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => setEditingAccount(account)}
                        className="text-blue-600 hover:text-blue-900"
                        title="Edit"
                      >
                        <FiEdit size={18} />
                      </button>
                      <button
                        onClick={() => {
                          const newPassword = prompt('Enter new password (min 12 characters):');
                          if (newPassword && newPassword.length >= 12) {
                            resetPasswordMutation.mutate({ uid: account.uid, password: newPassword });
                          } else if (newPassword) {
                            setToast({
                              type: 'error',
                              message: 'Password must be at least 12 characters',
                              duration: 3000,
                            });
                          }
                        }}
                        className="text-purple-600 hover:text-purple-900"
                        title="Reset Password"
                      >
                        <FiKey size={18} />
                      </button>
                      <button
                        onClick={() => handleDelete(account.uid)}
                        className="text-red-600 hover:text-red-900"
                        title="Delete"
                      >
                        <FiTrash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {data && (
        <div className="mt-6 flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Showing {data.items?.length || 0} of {data.total} service accounts
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(page + 1)}
              disabled={!data.items || data.items.length < 20}
              className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50"
            >
              Next
            </button>
          </div>
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

export default ServiceAccounts;

