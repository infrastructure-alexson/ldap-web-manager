/**
 * Dashboard Page
 */

import React from 'react';
import { FiUsers, FiGrid, FiGlobe, FiServer } from 'react-icons/fi';

const Dashboard = () => {
  const stats = [
    { name: 'Total Users', value: '—', icon: FiUsers, color: 'bg-blue-500' },
    { name: 'Groups', value: '—', icon: FiGrid, color: 'bg-green-500' },
    { name: 'DNS Zones', value: '—', icon: FiGlobe, color: 'bg-purple-500' },
    { name: 'DHCP Subnets', value: '—', icon: FiServer, color: 'bg-orange-500' },
  ];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Overview of your infrastructure
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center">
              <div className={`p-3 rounded-lg ${stat.color}`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Welcome Card */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Welcome to LDAP Web Manager</h2>
        <p className="text-gray-600 mb-4">
          This is your central management interface for:
        </p>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li>User & Group Management (LDAP)</li>
          <li>DNS Zone & Record Management (BIND 9)</li>
          <li>DHCP Subnet & Host Management (Kea)</li>
          <li>IP Address Management (IPAM)</li>
        </ul>
        <p className="mt-4 text-sm text-gray-500">
          Select an option from the sidebar to get started.
        </p>
      </div>
    </div>
  );
};

export default Dashboard;

