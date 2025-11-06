/**
 * Main Layout Component
 * Sidebar navigation and content area
 */

import React from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import {
  FiHome,
  FiUsers,
  FiGrid,
  FiGlobe,
  FiServer,
  FiMapPin,
  FiLock,
  FiClipboard,
  FiZap,
  FiSearch,
  FiCalculator,
  FiLogOut,
  FiMenu,
  FiMoon,
  FiSun,
} from 'react-icons/fi';

const Layout = () => {
  const { user, logout } = useAuth();
  const { isDarkMode, toggleTheme } = useTheme();
  const [sidebarOpen, setSidebarOpen] = React.useState(true);

  const navigation = [
    { name: 'Dashboard', href: '/', icon: FiHome },
    { name: 'Users', href: '/users', icon: FiUsers },
    { name: 'Groups', href: '/groups', icon: FiGrid },
    { name: 'Service Accounts', href: '/service-accounts', icon: FiLock },
    { name: 'Audit Logs', href: '/audit-logs', icon: FiClipboard },
    { name: 'Bulk Operations', href: '/bulk-operations', icon: FiZap },
    { name: 'Pool Management', href: '/pool-management', icon: FiMapPin },
    { name: 'IP Search', href: '/ip-search', icon: FiSearch },
    { name: 'Subnet Calculator', href: '/subnet-calculator', icon: FiCalculator },
    { name: 'DNS', href: '/dns', icon: FiGlobe },
    { name: 'DHCP', href: '/dhcp', icon: FiServer },
    { name: 'IPAM', href: '/ipam', icon: FiMapPin },
  ];

  return (
    <div className={`min-h-screen ${isDarkMode ? 'dark bg-gray-900' : 'bg-gray-50'}`}>
      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-64 shadow-lg transform transition-transform duration-300 ease-in-out ${
          isDarkMode ? 'dark bg-gray-800' : 'bg-white'
        } ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="flex flex-col h-full">
          {/* Logo/Header */}
          <div className={`flex items-center justify-between h-16 px-6 border-b ${isDarkMode ? 'border-gray-700' : ''}`}>
            <h1 className="text-xl font-bold text-primary-600">
              LDAP Manager
            </h1>
            <button
              onClick={() => setSidebarOpen(false)}
              className={`lg:hidden ${isDarkMode ? 'text-gray-400' : ''}`}
            >
              <FiMenu className="w-6 h-6" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  `flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? isDarkMode ? 'bg-gray-700 text-primary-400' : 'bg-primary-50 text-primary-700'
                      : isDarkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-100'
                  }`
                }
              >
                <item.icon className="w-5 h-5 mr-3" />
                {item.name}
              </NavLink>
            ))}
          </nav>

          {/* User info & Theme toggle */}
          <div className={`p-4 border-t ${isDarkMode ? 'border-gray-700' : ''}`}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
                  <span className="text-primary-600 font-semibold">
                    {user?.username?.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-medium truncate ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                    {user?.username}
                  </p>
                  <p className={`text-xs truncate ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                    {user?.role}
                  </p>
                </div>
              </div>
              <button
                onClick={logout}
                className={`p-2 transition-colors ${isDarkMode ? 'text-gray-400 hover:text-red-400' : 'text-gray-400 hover:text-red-600'}`}
                title="Logout"
              >
                <FiLogOut className="w-5 h-5" />
              </button>
            </div>
            
            {/* Theme toggle */}
            <button
              onClick={toggleTheme}
              className={`w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                isDarkMode
                  ? 'bg-gray-700 text-gray-200 hover:bg-gray-600'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
              title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {isDarkMode ? (
                <>
                  <FiSun className="w-4 h-4" />
                  <span className="text-xs font-medium">Light</span>
                </>
              ) : (
                <>
                  <FiMoon className="w-4 h-4" />
                  <span className="text-xs font-medium">Dark</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className={`transition-all duration-300 ${sidebarOpen ? 'lg:ml-64' : ''}`}>
        {/* Top bar */}
        <div className={`sticky top-0 z-40 h-16 border-b flex items-center px-6 transition-colors ${
          isDarkMode ? 'dark bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        }`}>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className={`p-2 rounded-md transition-colors ${
              isDarkMode
                ? 'text-gray-400 hover:text-gray-300 hover:bg-gray-700'
                : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
            }`}
          >
            <FiMenu className="w-6 h-6" />
          </button>
        </div>

        {/* Page content */}
        <main className={`p-6 ${isDarkMode ? 'dark' : ''}`}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;

