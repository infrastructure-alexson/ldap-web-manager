/**
 * Group Details Modal
 * 
 * Display detailed group information and members
 */

import React, { useState } from 'react';
import { FiX, FiTrash2, FiUserPlus } from 'react-icons/fi';
import Toast from './Toast';
import apiClient from '../api/client';
import { useTheme } from '../contexts/ThemeContext';

const GroupDetailsModal = ({ group, onClose, onSuccess }) => {
  const { isDarkMode } = useTheme();
  const [members, setMembers] = useState(group?.members || []);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [newMember, setNewMember] = useState('');

  const handleAddMember = async () => {
    if (!newMember.trim()) return;

    setLoading(true);
    try {
      await apiClient.post(`/api/groups/${group.id}/members`, { username: newMember });
      setMembers([...members, newMember]);
      setNewMember('');
      setToast({ type: 'success', message: `${newMember} added to group`, duration: 2000 });
    } catch (error) {
      setToast({ type: 'error', message: 'Failed to add member', duration: 3000 });
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveMember = async (username) => {
    try {
      await apiClient.delete(`/api/groups/${group.id}/members/${username}`);
      setMembers(members.filter(m => m !== username));
      setToast({ type: 'success', message: `${username} removed from group`, duration: 2000 });
    } catch (error) {
      setToast({ type: 'error', message: 'Failed to remove member', duration: 3000 });
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className={`card w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-lg shadow-xl ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
        {/* Header */}
        <div className="flex justify-between items-center mb-6 pb-6 border-b sticky top-0" style={{borderColor: isDarkMode ? '#374151' : '#e5e7eb'}}>
          <div>
            <h2 className={`text-2xl font-bold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>{group?.name}</h2>
            <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>{group?.description}</p>
          </div>
          <button onClick={onClose} className={`p-2 rounded-lg transition ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}>
            <FiX className="w-6 h-6" />
          </button>
        </div>

        <div className="space-y-6">
          {/* Group Info */}
          <div>
            <h3 className={`font-semibold mb-4 ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>Group Information</h3>
            <div className={`grid grid-cols-2 gap-4 p-4 rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
              <div>
                <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Group Name</p>
                <p className={`font-semibold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>{group?.name}</p>
              </div>
              <div>
                <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Members</p>
                <p className={`font-semibold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>{members.length}</p>
              </div>
            </div>
          </div>

          {/* Add Member */}
          <div>
            <h3 className={`font-semibold mb-4 ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>Add Member</h3>
            <div className="flex gap-2">
              <input
                type="text"
                value={newMember}
                onChange={(e) => setNewMember(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddMember()}
                placeholder="Enter username"
                className={`flex-1 px-3 py-2 rounded-lg border transition ${
                  isDarkMode ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-white border-gray-300'
                } focus:outline-none focus:ring-2 focus:ring-blue-500`}
              />
              <button
                onClick={handleAddMember}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium flex items-center gap-2 disabled:opacity-50"
              >
                <FiUserPlus size={18} /> Add
              </button>
            </div>
          </div>

          {/* Members List */}
          <div>
            <h3 className={`font-semibold mb-4 ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>Members ({members.length})</h3>
            {members.length > 0 ? (
              <div className="space-y-2">
                {members.map(username => (
                  <div key={username} className={`flex items-center justify-between p-3 rounded-lg ${isDarkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-50 hover:bg-gray-100'}`}>
                    <span className={isDarkMode ? 'text-gray-100' : 'text-gray-900'}>{username}</span>
                    <button
                      onClick={() => handleRemoveMember(username)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <FiTrash2 size={18} />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className={`text-center py-8 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>No members in this group</p>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 pt-6 border-t mt-6" style={{borderColor: isDarkMode ? '#374151' : '#e5e7eb'}}>
          <button
            onClick={onClose}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition ${
              isDarkMode ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Close
          </button>
        </div>

        {toast && <Toast type={toast.type} message={toast.message} duration={toast.duration} onClose={() => setToast(null)} />}
      </div>
    </div>
  );
};

export default GroupDetailsModal;

