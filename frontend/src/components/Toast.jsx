import React, { useEffect } from 'react';
import { FiAlertCircle, FiCheckCircle, FiInfo, FiX } from 'react-icons/fi';

/**
 * Toast Component
 * 
 * Displays temporary notification messages at the top or bottom of the screen.
 * Supports success, error, info, and warning types.
 */
const Toast = ({ 
  type = 'info', 
  message, 
  duration = 3000, 
  onClose,
  position = 'top-right' 
}) => {
  useEffect(() => {
    if (duration) {
      const timer = setTimeout(onClose, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  const bgColors = {
    success: 'bg-green-50 border-green-200',
    error: 'bg-red-50 border-red-200',
    info: 'bg-blue-50 border-blue-200',
    warning: 'bg-yellow-50 border-yellow-200',
  };

  const textColors = {
    success: 'text-green-800',
    error: 'text-red-800',
    info: 'text-blue-800',
    warning: 'text-yellow-800',
  };

  const iconColors = {
    success: 'text-green-600',
    error: 'text-red-600',
    info: 'text-blue-600',
    warning: 'text-yellow-600',
  };

  const icons = {
    success: <FiCheckCircle size={20} />,
    error: <FiAlertCircle size={20} />,
    info: <FiInfo size={20} />,
    warning: <FiAlertCircle size={20} />,
  };

  const positionClasses = {
    'top-left': 'top-4 left-4',
    'top-right': 'top-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'bottom-right': 'bottom-4 right-4',
  };

  return (
    <div
      className={`fixed ${positionClasses[position]} z-50 animate-slideIn`}
    >
      <div
        className={`flex items-center gap-3 p-4 rounded-lg border ${bgColors[type]} shadow-lg max-w-sm`}
      >
        <div className={iconColors[type]}>
          {icons[type]}
        </div>
        <p className={`text-sm font-medium ${textColors[type]} flex-1`}>
          {message}
        </p>
        <button
          onClick={onClose}
          className={`p-1 hover:bg-opacity-50 rounded transition ${textColors[type]}`}
        >
          <FiX size={16} />
        </button>
      </div>
    </div>
  );
};

export default Toast;


