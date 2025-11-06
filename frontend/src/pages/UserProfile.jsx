/**
 * User Profile Page
 * 
 * Display and manage current user profile and settings
 */

import React, { useState, useEffect } from 'react';
import { FiUser, FiMail, FiEdit2, FiSave, FiX, FiLock } from 'react-icons/fi';
import Toast from '../components/Toast';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import apiClient from '../api/client';

const UserProfile = () => {
  const { user } = useAuth();
  const { isDarkMode } = useTheme();
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [showPasswordModal, setShowPasswordModal] = useState(false);

  const [profileData, setProfileData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    full_name: user?.full_name || '',
    mail: user?.mail || '',
    description: user?.description || ''
  });

  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfileData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSaveProfile = async () => {
    setLoading(true);
    try {
      await apiClient.put(`/api/users/${user.username}`, profileData);
      setToast({ type: 'success', message: 'Profile updated successfully', duration: 3000 });
      setIsEditing(false);
    } catch (error) {
      setToast({ type: 'error', message: 'Failed to update profile', duration: 3000 });
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async () => {
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setToast({ type: 'error', message: 'Passwords do not match', duration: 3000 });
      return;
    }

    setLoading(true);
    try {
      await apiClient.post(`/api/users/${user.username}/reset-password`, {
        new_password: passwordData.newPassword
      });
      setToast({ type: 'success', message: 'Password changed successfully', duration: 3000 });
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
      setShowPasswordModal(false);
    } catch (error) {
      setToast({ type: 'error', message: 'Failed to change password', duration: 3000 });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className={`text-4xl font-bold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
          User Profile
        </h1>
        <p className={`mt-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
          Manage your account and personal information
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Card */}
        <div className={`lg:col-span-2 card ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
          <div className="flex justify-between items-center mb-6 pb-6 border-b" style={{borderColor: isDarkMode ? '#374151' : '#e5e7eb'}}>
            <h2 className={`text-2xl font-bold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
              Profile Information
            </h2>
            {!isEditing && (
              <button
                onClick={() => setIsEditing(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition"
              >
                <FiEdit2 size={18} />
                Edit Profile
              </button>
            )}
          </div>

          <div className="space-y-6">
            {/* Avatar */}
            <div className="flex items-center gap-4">
              <div className={`w-20 h-20 rounded-full flex items-center justify-center text-2xl font-bold ${
                isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700'
              }`}>
                {user?.username?.charAt(0).toUpperCase()}
              </div>
              <div>
                <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Username</p>
                <p className={`text-xl font-semibold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                  {profileData.username}
                </p>
              </div>
            </div>

            {/* Profile Fields */}
            <div className="space-y-4">
              {isEditing ? (
                <>
                  <div>
                    <label className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                      Full Name
                    </label>
                    <input
                      type="text"
                      name="full_name"
                      value={profileData.full_name}
                      onChange={handleProfileChange}
                      placeholder="Enter your full name"
                      className={`w-full px-4 py-2 rounded-lg border transition ${
                        isDarkMode ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-white border-gray-300'
                      } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                    />
                  </div>

                  <div>
                    <label className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                      Email
                    </label>
                    <input
                      type="email"
                      name="mail"
                      value={profileData.mail}
                      onChange={handleProfileChange}
                      placeholder="Enter your email"
                      className={`w-full px-4 py-2 rounded-lg border transition ${
                        isDarkMode ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-white border-gray-300'
                      } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                    />
                  </div>

                  <div>
                    <label className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                      Description
                    </label>
                    <textarea
                      name="description"
                      value={profileData.description}
                      onChange={handleProfileChange}
                      placeholder="Tell us about yourself..."
                      rows="3"
                      className={`w-full px-4 py-2 rounded-lg border transition ${
                        isDarkMode ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-white border-gray-300'
                      } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                    />
                  </div>

                  <div className="flex gap-3 pt-4">
                    <button
                      onClick={() => setIsEditing(false)}
                      className={`flex-1 px-4 py-2 rounded-lg font-medium transition ${
                        isDarkMode ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      <FiX size={18} className="inline mr-2" />
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveProfile}
                      disabled={loading}
                      className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition flex items-center justify-center gap-2"
                    >
                      <FiSave size={18} />
                      {loading ? 'Saving...' : 'Save Changes'}
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Full Name</p>
                    <p className={isDarkMode ? 'text-gray-100' : 'text-gray-900'}>{profileData.full_name || '-'}</p>
                  </div>

                  <div>
                    <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Email</p>
                    <p className={isDarkMode ? 'text-gray-100' : 'text-gray-900'}>{profileData.mail || '-'}</p>
                  </div>

                  <div>
                    <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Description</p>
                    <p className={isDarkMode ? 'text-gray-100' : 'text-gray-900'}>{profileData.description || '-'}</p>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Security Card */}
        <div className={`card ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
          <h3 className={`text-lg font-bold mb-4 ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
            Security
          </h3>

          <div className="space-y-4">
            <button
              onClick={() => setShowPasswordModal(true)}
              className="w-full flex items-center gap-2 px-4 py-3 rounded-lg font-medium transition bg-red-600 hover:bg-red-700 text-white"
            >
              <FiLock size={18} />
              Change Password
            </button>

            <div className={`p-4 rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-blue-50'}`}>
              <p className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-blue-900'}`}>
                Keep your account secure by using a strong, unique password.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Password Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className={`card w-full max-w-md rounded-lg shadow-xl ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
            <div className="flex justify-between items-center mb-4 pb-4 border-b" style={{borderColor: isDarkMode ? '#374151' : '#e5e7eb'}}>
              <h2 className={`text-xl font-bold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                Change Password
              </h2>
              <button onClick={() => setShowPasswordModal(false)} className={`p-1 rounded ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}>
                <FiX size={20} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  New Password
                </label>
                <input
                  type="password"
                  value={passwordData.newPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                  className={`w-full px-3 py-2 rounded-lg border transition ${
                    isDarkMode ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-white border-gray-300'
                  } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                />
              </div>

              <div>
                <label className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Confirm Password
                </label>
                <input
                  type="password"
                  value={passwordData.confirmPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                  className={`w-full px-3 py-2 rounded-lg border transition ${
                    isDarkMode ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-white border-gray-300'
                  } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => setShowPasswordModal(false)}
                  className={`flex-1 px-4 py-2 rounded-lg font-medium transition ${
                    isDarkMode ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Cancel
                </button>
                <button
                  onClick={handleChangePassword}
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition"
                >
                  {loading ? 'Updating...' : 'Update'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

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

export default UserProfile;

