/**
 * DNS Management Page
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { dnsApi } from '../api/dns';
import { FiPlus, FiSearch, FiGlobe, FiEdit, FiTrash2 } from 'react-icons/fi';

const DNS = () => {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  // Fetch DNS zones
  const { data, isLoading, error } = useQuery({
    queryKey: ['dns', 'zones', page, search],
    queryFn: () => dnsApi.listZones({ page, page_size: 20, search: search || undefined }),
  });

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">DNS Zones</h1>
          <p className="mt-2 text-gray-600">
            Manage DNS zones and records for BIND 9
          </p>
        </div>
        <button className="btn-primary flex items-center">
          <FiPlus className="mr-2" />
          Create Zone
        </button>
      </div>

      {/* Search */}
      <div className="mb-6 card">
        <div className="relative">
          <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search zones..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        </div>
      </div>

      {/* Zones Table */}
      <div className="card">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading DNS zones...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12 text-red-600">
            <FiGlobe className="mx-auto h-12 w-12 mb-4" />
            <p>Failed to load DNS zones</p>
          </div>
        ) : data?.zones?.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <FiGlobe className="mx-auto h-12 w-12 mb-4" />
            <p>No DNS zones found</p>
            <p className="mt-2 text-sm">Create your first DNS zone to get started</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Zone Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Primary NS
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Serial
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      SOA Settings
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data?.zones?.map((zone) => (
                    <tr key={zone.dn} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <FiGlobe className="text-purple-500 mr-2" />
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {zone.idnsName}
                            </div>
                            {zone.description && (
                              <div className="text-sm text-gray-500">
                                {zone.description}
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {zone.idnsSOAmName}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">
                          {zone.idnsSOAserial || '—'}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-xs text-gray-500">
                          <div>Refresh: {zone.idnsSOArefresh}s</div>
                          <div>Retry: {zone.idnsSOAretry}s</div>
                          <div>Expire: {zone.idnsSOAexpire}s</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          className="text-primary-600 hover:text-primary-900 mr-3"
                          title="Manage Records"
                        >
                          <FiEdit />
                        </button>
                        <button
                          className="text-red-600 hover:text-red-900"
                          title="Delete Zone"
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
                  Showing {((page - 1) * data.page_size) + 1} to {Math.min(page * data.page_size, data.total)} of {data.total} zones
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

export default DNS;

