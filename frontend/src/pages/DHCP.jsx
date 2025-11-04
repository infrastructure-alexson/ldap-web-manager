/**
 * DHCP Management Page
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { dhcpApi } from '../api/dhcp';
import { FiPlus, FiSearch, FiServer, FiEdit, FiTrash2, FiList } from 'react-icons/fi';

const DHCP = () => {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  // Fetch DHCP subnets
  const { data, isLoading, error } = useQuery({
    queryKey: ['dhcp', 'subnets', page, search],
    queryFn: () => dhcpApi.listSubnets({ page, page_size: 20, search: search || undefined }),
  });

  // Fetch DHCP stats
  const { data: statsData } = useQuery({
    queryKey: ['dhcp', 'stats'],
    queryFn: dhcpApi.getStats,
  });

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">DHCP Management</h1>
          <p className="mt-2 text-gray-600">
            Manage DHCP subnets and static reservations for Kea DHCP
          </p>
        </div>
        <button className="btn-primary flex items-center">
          <FiPlus className="mr-2" />
          Create Subnet
        </button>
      </div>

      {/* Statistics Cards */}
      {statsData && (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-6">
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-orange-500">
                <FiServer className="w-6 h-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Subnets</p>
                <p className="text-2xl font-semibold text-gray-900">{statsData.total_subnets}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-blue-500">
                <FiList className="w-6 h-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Static Hosts</p>
                <p className="text-2xl font-semibold text-gray-900">{statsData.total_static_hosts}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-green-500">
                <FiServer className="w-6 h-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total IPs</p>
                <p className="text-2xl font-semibold text-gray-900">{statsData.total_ip_addresses}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-purple-500">
                <FiServer className="w-6 h-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Utilization</p>
                <p className="text-2xl font-semibold text-gray-900">{statsData.utilization_percent}%</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="mb-6 card">
        <div className="relative">
          <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search subnets..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        </div>
      </div>

      {/* Subnets Table */}
      <div className="card">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading DHCP subnets...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12 text-red-600">
            <FiServer className="mx-auto h-12 w-12 mb-4" />
            <p>Failed to load DHCP subnets</p>
          </div>
        ) : data?.subnets?.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <FiServer className="mx-auto h-12 w-12 mb-4" />
            <p>No DHCP subnets found</p>
            <p className="mt-2 text-sm">Create your first subnet to get started</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Subnet
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Netmask
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Ranges
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Options
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data?.subnets?.map((subnet) => (
                    <tr key={subnet.dn} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <FiServer className="text-orange-500 mr-2" />
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {subnet.cn}/{subnet.dhcpNetMask}
                            </div>
                            {subnet.description && (
                              <div className="text-sm text-gray-500">
                                {subnet.description}
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {subnet.dhcpNetMask}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-500">
                          {subnet.dhcpRange?.length > 0 ? (
                            subnet.dhcpRange.map((range, idx) => (
                              <div key={idx}>{range}</div>
                            ))
                          ) : (
                            '—'
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-xs text-gray-500">
                          {subnet.dhcpOption?.length > 0 ? (
                            <span>{subnet.dhcpOption.length} options</span>
                          ) : (
                            '—'
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          className="text-primary-600 hover:text-primary-900 mr-3"
                          title="View Static Hosts"
                        >
                          <FiList />
                        </button>
                        <button
                          className="text-blue-600 hover:text-blue-900 mr-3"
                          title="Edit Subnet"
                        >
                          <FiEdit />
                        </button>
                        <button
                          className="text-red-600 hover:text-red-900"
                          title="Delete Subnet"
                        >
                          <FiTrash2 />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {data && data.total > data.page_size && (
              <div className="mt-4 flex items-center justify-between border-t pt-4">
                <div className="text-sm text-gray-700">
                  Showing {((page - 1) * data.page_size) + 1} to {Math.min(page * data.page_size, data.total)} of {data.total} subnets
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-4 py-2 border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage(p => p + 1)}
                    disabled={page * data.page_size >= data.total}
                    className="px-4 py-2 border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default DHCP;

