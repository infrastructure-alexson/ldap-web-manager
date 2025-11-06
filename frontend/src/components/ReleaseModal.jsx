import React, { useState } from 'react';
import { FiX, FiAlertTriangle } from 'react-icons/fi';

/**
 * ReleaseModal Component
 * 
 * Confirmation modal for releasing an allocated IP address.
 * Displays a warning and requires confirmation before release.
 */
const ReleaseModal = ({ ip, onConfirm, onCancel }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirmText, setConfirmText] = useState('');
  const [error, setError] = useState('');

  const handleConfirm = async () => {
    // Require confirmation by typing IP address
    if (confirmText !== ip.ip_address) {
      setError('Please enter the correct IP address to confirm release');
      return;
    }

    setIsSubmitting(true);
    try {
      await onConfirm();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-md w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-red-200 bg-red-50">
          <div className="flex items-center gap-3">
            <FiAlertTriangle size={24} className="text-red-600" />
            <h2 className="text-xl font-bold text-gray-900">Release IP Address</h2>
          </div>
          <button
            onClick={onCancel}
            className="p-1 hover:bg-red-100 rounded transition"
          >
            <FiX size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Warning Message */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-sm text-yellow-800">
              <strong>Warning:</strong> This will release the IP address back to the available pool. 
              This action is generally permanent and cannot be easily undone.
            </p>
          </div>

          {/* IP Information */}
          <div className="space-y-2">
            <h3 className="font-semibold text-gray-900">IP Address Details</h3>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500">IP Address</p>
                <p className="font-mono font-bold text-gray-900">{ip.ip_address}</p>
              </div>
              
              <div>
                <p className="text-gray-500">Status</p>
                <p className="font-semibold text-blue-900">Allocated</p>
              </div>

              {ip.hostname && (
                <div>
                  <p className="text-gray-500">Hostname</p>
                  <p className="font-mono text-gray-900">{ip.hostname}</p>
                </div>
              )}

              {ip.owner && (
                <div>
                  <p className="text-gray-500">Owner</p>
                  <p className="text-gray-900">{ip.owner}</p>
                </div>
              )}

              {ip.mac_address && (
                <div>
                  <p className="text-gray-500">MAC Address</p>
                  <p className="font-mono text-gray-900">{ip.mac_address}</p>
                </div>
              )}

              {ip.purpose && (
                <div>
                  <p className="text-gray-500">Purpose</p>
                  <p className="text-gray-900 capitalize">{ip.purpose}</p>
                </div>
              )}
            </div>
          </div>

          {/* Confirmation Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Type the IP address to confirm release:
            </label>
            <input
              type="text"
              value={confirmText}
              onChange={(e) => {
                setConfirmText(e.target.value);
                if (error) setError('');
              }}
              placeholder={ip.ip_address}
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono ${
                error ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {error && (
              <p className="mt-2 text-sm text-red-600">{error}</p>
            )}
          </div>

          {/* Info Text */}
          <p className="text-xs text-gray-500">
            This confirmation is required to prevent accidental releases. 
            After release, the IP will be marked as available for allocation.
          </p>
        </div>

        {/* Actions */}
        <div className="flex gap-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onCancel}
            disabled={isSubmitting}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={isSubmitting || !confirmText}
            className="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 disabled:bg-red-400 text-white rounded-lg transition"
          >
            {isSubmitting ? 'Releasing...' : 'Release IP'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReleaseModal;


