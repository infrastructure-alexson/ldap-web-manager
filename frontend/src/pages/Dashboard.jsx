/**
 * Dashboard Page
 */

import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FiUsers, FiGrid, FiGlobe, FiServer, FiActivity, FiAlertCircle } from 'react-icons/fi';
import { usersApi } from '../api/users';
import { groupsApi } from '../api/groups';
import { dnsApi } from '../api/dns';

const Dashboard = () => {
  // Fetch statistics
  const { data: usersData, isLoading: usersLoading } = useQuery({
    queryKey: ['users', 'stats'],
    queryFn: () => usersApi.list({ page: 1, page_size: 1 }),
  });

  const { data: groupsData, isLoading: groupsLoading } = useQuery({
    queryKey: ['groups', 'stats'],
    queryFn: () => groupsApi.list({ page: 1, page_size: 1 }),
  });

  const { data: dnsData, isLoading: dnsLoading } = useQuery({
    queryKey: ['dns', 'stats'],
    queryFn: () => dnsApi.listZones({ page: 1, page_size: 1 }),
  });

  const stats = [
    { 
      name: 'Total Users', 
      value: usersLoading ? '—' : usersData?.total || 0, 
      icon: FiUsers, 
      color: 'bg-blue-500',
      href: '/users'
    },
    { 
      name: 'Groups', 
      value: groupsLoading ? '—' : groupsData?.total || 0, 
      icon: FiGrid, 
      color: 'bg-green-500',
      href: '/groups'
    },
    { 
      name: 'DNS Zones', 
      value: dnsLoading ? '—' : dnsData?.total || 0, 
      icon: FiGlobe, 
      color: 'bg-purple-500',
      href: '/dns'
    },
    { 
      name: 'DHCP Subnets', 
      value: '—', 
      icon: FiServer, 
      color: 'bg-orange-500',
      href: '/dhcp'
    },
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
          <a
            key={stat.name}
            href={stat.href}
            className="card hover:shadow-md transition-shadow cursor-pointer"
          >
            <div className="flex items-center">
              <div className={`p-3 rounded-lg ${stat.color}`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </a>
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

