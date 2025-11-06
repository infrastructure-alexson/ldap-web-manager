/**
 * Dashboard Page
 * 
 * Main dashboard with statistics widgets and activity overview
 */

import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  FiUsers, FiGrid, FiGlobe, FiServer, FiActivity, FiAlertCircle,
  FiTrendingUp, FiArrowRight, FiRefreshCw, FiMapPin, FiLock, FiClipboard
} from 'react-icons/fi';
import { usersApi } from '../api/users';
import { groupsApi } from '../api/groups';
import { dnsApi } from '../api/dns';
import { dhcpApi } from '../api/dhcp';
import { useTheme } from '../contexts/ThemeContext';

const Dashboard = () => {
  const { isDarkMode } = useTheme();

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

  const { data: dhcpData, isLoading: dhcpLoading } = useQuery({
    queryKey: ['dhcp', 'stats'],
    queryFn: dhcpApi.getStats,
  });

  const stats = [
    { 
      name: 'Total Users', 
      value: usersLoading ? '—' : usersData?.total || 0, 
      icon: FiUsers, 
      color: 'bg-blue-500',
      lightColor: 'bg-blue-50',
      textColor: 'text-blue-700',
      href: '/users',
      trend: '+12% this month'
    },
    { 
      name: 'Groups', 
      value: groupsLoading ? '—' : groupsData?.total || 0, 
      icon: FiGrid, 
      color: 'bg-green-500',
      lightColor: 'bg-green-50',
      textColor: 'text-green-700',
      href: '/groups',
      trend: '+3 this week'
    },
    { 
      name: 'DNS Zones', 
      value: dnsLoading ? '—' : dnsData?.total || 0, 
      icon: FiGlobe, 
      color: 'bg-purple-500',
      lightColor: 'bg-purple-50',
      textColor: 'text-purple-700',
      href: '/dns',
      trend: '+5 records'
    },
    { 
      name: 'DHCP Subnets', 
      value: dhcpLoading ? '—' : dhcpData?.total_subnets || 0, 
      icon: FiServer, 
      color: 'bg-orange-500',
      lightColor: 'bg-orange-50',
      textColor: 'text-orange-700',
      href: '/dhcp',
      trend: '95% utilization'
    },
    {
      name: 'Service Accounts',
      value: 8,
      icon: FiLock,
      color: 'bg-red-500',
      lightColor: 'bg-red-50',
      textColor: 'text-red-700',
      href: '/service-accounts',
      trend: 'All active'
    },
    {
      name: 'Audit Logs',
      value: '2.4K',
      icon: FiClipboard,
      color: 'bg-indigo-500',
      lightColor: 'bg-indigo-50',
      textColor: 'text-indigo-700',
      href: '/audit-logs',
      trend: 'Last 24 hours'
    }
  ];

  const quickActions = [
    {
      title: 'Create User',
      description: 'Add a new user to the system',
      icon: FiUsers,
      href: '/users',
      color: 'blue'
    },
    {
      title: 'Create Group',
      description: 'Organize users into groups',
      icon: FiGrid,
      href: '/groups',
      color: 'green'
    },
    {
      title: 'Manage DNS',
      description: 'Configure DNS zones and records',
      icon: FiGlobe,
      href: '/dns',
      color: 'purple'
    },
    {
      title: 'Manage DHCP',
      description: 'Configure DHCP subnets',
      icon: FiServer,
      href: '/dhcp',
      color: 'orange'
    },
    {
      title: 'IP Management',
      description: 'Allocate and track IP addresses',
      icon: FiMapPin,
      href: '/ipam',
      color: 'pink'
    },
    {
      title: 'Bulk Operations',
      description: 'Perform batch operations',
      icon: FiActivity,
      href: '/bulk-operations',
      color: 'cyan'
    }
  ];

  const colorClasses = {
    blue: 'hover:bg-blue-50 dark:hover:bg-gray-700',
    green: 'hover:bg-green-50 dark:hover:bg-gray-700',
    purple: 'hover:bg-purple-50 dark:hover:bg-gray-700',
    orange: 'hover:bg-orange-50 dark:hover:bg-gray-700',
    pink: 'hover:bg-pink-50 dark:hover:bg-gray-700',
    cyan: 'hover:bg-cyan-50 dark:hover:bg-gray-700'
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className={`text-4xl font-bold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
          Dashboard
        </h1>
        <p className={`mt-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
          Welcome back! Here's an overview of your infrastructure.
        </p>
      </div>

      {/* Stats Grid - 6 columns */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 mb-8">
        {stats.map((stat) => (
          <a
            key={stat.name}
            href={stat.href}
            className={`card group hover:shadow-lg transition-all duration-200 transform hover:scale-105 cursor-pointer ${
              isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-50'
            }`}
          >
            <div className="flex flex-col h-full">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-2 rounded-lg ${stat.color}`}>
                  <stat.icon className="w-5 h-5 text-white" />
                </div>
                <FiTrendingUp className={`w-4 h-4 ${isDarkMode ? 'text-gray-500 group-hover:text-green-400' : 'text-gray-400 group-hover:text-green-600'} transition-colors`} />
              </div>
              <p className={`text-xs font-medium mb-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                {stat.name}
              </p>
              <p className={`text-2xl font-bold mb-2 ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                {stat.value}
              </p>
              <p className={`text-xs ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                {stat.trend}
              </p>
            </div>
          </a>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className={`text-2xl font-bold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
            Quick Actions
          </h2>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {quickActions.map((action) => (
            <a
              key={action.title}
              href={action.href}
              className={`p-4 rounded-lg border transition-all duration-200 group ${
                isDarkMode
                  ? `border-gray-700 ${colorClasses[action.color]} hover:border-gray-600`
                  : `border-gray-200 ${colorClasses[action.color]} hover:border-gray-300`
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className={`font-semibold mb-1 group-hover:text-blue-600 transition-colors ${
                    isDarkMode ? 'text-gray-100' : 'text-gray-900'
                  }`}>
                    {action.title}
                  </h3>
                  <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                    {action.description}
                  </p>
                </div>
                <action.icon className={`w-5 h-5 flex-shrink-0 ml-2 transition-transform group-hover:translate-x-1 ${
                  isDarkMode ? 'text-gray-500' : 'text-gray-400'
                }`} />
              </div>
            </a>
          ))}
        </div>
      </div>

      {/* Information Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* About Card */}
        <div className="card">
          <h2 className={`text-xl font-bold mb-4 flex items-center gap-2 ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
            <FiActivity className="w-6 h-6" />
            System Overview
          </h2>
          <div className={`space-y-3 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            <p>
              LDAP Web Manager is your central management interface for your complete infrastructure:
            </p>
            <ul className="space-y-2 list-none">
              <li className="flex items-start gap-2">
                <span className="text-blue-500 mt-1">✓</span>
                <span><strong className={isDarkMode ? 'text-gray-300' : 'text-gray-900'}>User & Group Management:</strong> Manage all users, groups, and service accounts with LDAP backend</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-1">✓</span>
                <span><strong className={isDarkMode ? 'text-gray-300' : 'text-gray-900'}>DNS Management:</strong> Create and manage DNS zones and records with BIND 9</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-orange-500 mt-1">✓</span>
                <span><strong className={isDarkMode ? 'text-gray-300' : 'text-gray-900'}>DHCP Management:</strong> Configure DHCP subnets and host reservations with Kea</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-500 mt-1">✓</span>
                <span><strong className={isDarkMode ? 'text-gray-300' : 'text-gray-900'}>IP Address Management:</strong> Track, allocate, and manage IP addresses with visual interface</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Recent Activity Card */}
        <div className="card">
          <h2 className={`text-xl font-bold mb-4 flex items-center gap-2 ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
            <FiClipboard className="w-6 h-6" />
            Getting Started
          </h2>
          <div className={`space-y-3 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            <p>
              New to LDAP Web Manager? Here are some helpful resources:
            </p>
            <ul className="space-y-2 list-none">
              <li className="flex items-center gap-2">
                <FiArrowRight className="w-4 h-4" />
                <a href="/users" className={`${isDarkMode ? 'hover:text-blue-400' : 'hover:text-blue-600'} transition-colors`}>
                  Create your first user
                </a>
              </li>
              <li className="flex items-center gap-2">
                <FiArrowRight className="w-4 h-4" />
                <a href="/groups" className={`${isDarkMode ? 'hover:text-blue-400' : 'hover:text-blue-600'} transition-colors`}>
                  Organize users into groups
                </a>
              </li>
              <li className="flex items-center gap-2">
                <FiArrowRight className="w-4 h-4" />
                <a href="/dns" className={`${isDarkMode ? 'hover:text-blue-400' : 'hover:text-blue-600'} transition-colors`}>
                  Set up DNS zones
                </a>
              </li>
              <li className="flex items-center gap-2">
                <FiArrowRight className="w-4 h-4" />
                <a href="/audit-logs" className={`${isDarkMode ? 'hover:text-blue-400' : 'hover:text-blue-600'} transition-colors`}>
                  View audit logs
                </a>
              </li>
            </ul>
            <div className={`mt-4 p-3 rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-blue-50'}`}>
              <p className="text-sm flex items-start gap-2">
                <FiAlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>Need help? Check the documentation or contact your administrator.</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
