import React, { useState } from 'react';
import { FiPlus, FiTrash2, FiRefreshCw } from 'react-icons/fi';
import AllocationModal from './AllocationModal';
import ReleaseModal from './ReleaseModal';

/**
 * IPAllocationGrid Component
 * 
 * Displays IP addresses in a grid with color-coded status indicators.
 * Supports allocation, release, and filtering of IP addresses.
 */
const IPAllocationGrid = ({ 
  allocations = [], 
  pool,
  onAllocate,
  onRelease,
  onRefresh,
  isLoading = false 
}) => {
  const [selectedIP, setSelectedIP] = useState(null);
  const [showAllocateModal, setShowAllocateModal] = useState(false);
  const [showReleaseModal, setShowReleaseModal] = useState(false);
  const [searchFilter, setSearchFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Status color mapping
  const statusColors = {
    available: 'bg-green-100 border-green-300 text-green-900 hover:bg-green-200',
    allocated: 'bg-blue-100 border-blue-300 text-blue-900 hover:bg-blue-200',
    reserved: 'bg-yellow-100 border-yellow-300 text-yellow-900 hover:bg-yellow-200',
    blocked: 'bg-red-100 border-red-300 text-red-900 hover:bg-red-200',
  };

  const statusBadges = {
    available: 'Available',
    allocated: 'Allocated',
    reserved: 'Reserved',
    blocked: 'Blocked',
  };

  // Filter allocations based on search and status
  const filteredAllocations = allocations.filter(alloc => {
    const matchesSearch = 
      alloc.ip_address.includes(searchFilter) ||
      (alloc.hostname && alloc.hostname.toLowerCase().includes(searchFilter.toLowerCase())) ||
      (alloc.owner && alloc.owner.toLowerCase().includes(searchFilter.toLowerCase()));
    
    const matchesStatus = statusFilter === 'all' || alloc.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  // Sort allocations by IP address
  const sortedAllocations = [...filteredAllocations].sort((a, b) => {
    const aIP = a.ip_address.split('.').map(Number);
    const bIP = b.ip_address.split('.').map(Number);
    
    for (let i = 0; i < 4; i++) {
      if (aIP[i] !== bIP[i]) return aIP[i] - bIP[i];
    }
    return 0;
  });

  // Handle allocation action
  const handleAllocate = (ip) => {
    setSelectedIP(ip);
    setShowAllocateModal(true);
  };

  // Handle release action
  const handleRelease = (ip) => {
    setSelectedIP(ip);
    setShowReleaseModal(true);
  };

  // Handle confirm allocation
  const handleConfirmAllocate = async (data) => {
    try {
      await onAllocate(selectedIP.id, data);
      setShowAllocateModal(false);
      setSelectedIP(null);
    } catch (error) {
      console.error('Failed to allocate IP:', error);
    }
  };

  // Handle confirm release
  const handleConfirmRelease = async () => {
    try {
      await onRelease(selectedIP.id);
      setShowReleaseModal(false);
      setSelectedIP(null);
    } catch (error) {
      console.error('Failed to release IP:', error);
    }
  };

  // Calculate statistics
  const stats = {
    total: allocations.length,
    available: allocations.filter(a => a.status === 'available').length,
    allocated: allocations.filter(a => a.status === 'allocated').length,
    reserved: allocations.filter(a => a.status === 'reserved').length,
    blocked: allocations.filter(a => a.status === 'blocked').length,
  };

  return (
    <div className="space-y-6">
      {/* Statistics */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <p className="text-sm font-medium text-gray-600">Total</p>
          <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
        </div>
        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <p className="text-sm font-medium text-green-700">Available</p>
          <p className="text-2xl font-bold text-green-900">{stats.available}</p>
        </div>
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <p className="text-sm font-medium text-blue-700">Allocated</p>
          <p className="text-2xl font-bold text-blue-900">{stats.allocated}</p>
        </div>
        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
          <p className="text-sm font-medium text-yellow-700">Reserved</p>
          <p className="text-2xl font-bold text-yellow-900">{stats.reserved}</p>
        </div>
        <div className="bg-red-50 p-4 rounded-lg border border-red-200">
          <p className="text-sm font-medium text-red-700">Blocked</p>
          <p className="text-2xl font-bold text-red-900">{stats.blocked}</p>
        </div>
      </div>

      {/* Filters and Controls */}
      <div className="bg-white p-4 rounded-lg border border-gray-200 space-y-4">
        <div className="flex gap-4 flex-wrap">
          {/* Search */}
          <input
            type="text"
            placeholder="Search by IP, hostname, or owner..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="flex-1 min-w-48 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Status</option>
            <option value="available">Available</option>
            <option value="allocated">Allocated</option>
            <option value="reserved">Reserved</option>
            <option value="blocked">Blocked</option>
          </select>

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="px-4 py-2 bg-gray-500 hover:bg-gray-600 disabled:bg-gray-400 text-white rounded-lg transition flex items-center gap-2"
          >
            <FiRefreshCw className={isLoading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>

        {/* Results Summary */}
        <p className="text-sm text-gray-600">
          Showing {sortedAllocations.length} of {allocations.length} IP addresses
        </p>
      </div>

      {/* IP Grid */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {sortedAllocations.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <p>No IP addresses found matching your filters</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <div className="grid gap-2 p-4 auto-grid-fit" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))' }}>
              {sortedAllocations.map((alloc) => (
                <div
                  key={alloc.id}
                  className={`p-3 rounded-lg border-2 cursor-pointer transition transform hover:scale-105 ${statusColors[alloc.status] || statusColors.available}`}
                >
                  {/* IP Address */}
                  <p className="font-mono font-bold text-sm mb-1">{alloc.ip_address}</p>
                  
                  {/* Status Badge */}
                  <div className="mb-2">
                    <span className="inline-block px-2 py-1 bg-white bg-opacity-50 rounded text-xs font-semibold">
                      {statusBadges[alloc.status]}
                    </span>
                  </div>

                  {/* Hostname (if available) */}
                  {alloc.hostname && (
                    <p className="text-xs truncate mb-1" title={alloc.hostname}>
                      {alloc.hostname}
                    </p>
                  )}

                  {/* Owner (if available) */}
                  {alloc.owner && (
                    <p className="text-xs text-opacity-75 mb-2">
                      Owner: {alloc.owner}
                    </p>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2 justify-center">
                    {alloc.status === 'available' && (
                      <button
                        onClick={() => handleAllocate(alloc)}
                        className="p-1 bg-blue-500 hover:bg-blue-600 text-white rounded transition"
                        title="Allocate"
                      >
                        <FiPlus size={14} />
                      </button>
                    )}
                    
                    {alloc.status === 'allocated' && (
                      <button
                        onClick={() => handleRelease(alloc)}
                        className="p-1 bg-red-500 hover:bg-red-600 text-white rounded transition"
                        title="Release"
                      >
                        <FiTrash2 size={14} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      {showAllocateModal && selectedIP && (
        <AllocationModal
          ip={selectedIP}
          onConfirm={handleConfirmAllocate}
          onCancel={() => setShowAllocateModal(false)}
        />
      )}

      {showReleaseModal && selectedIP && (
        <ReleaseModal
          ip={selectedIP}
          onConfirm={handleConfirmRelease}
          onCancel={() => setShowReleaseModal(false)}
        />
      )}
    </div>
  );
};

export default IPAllocationGrid;


