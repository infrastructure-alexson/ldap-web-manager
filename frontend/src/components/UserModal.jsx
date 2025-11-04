/**
 * User Create/Edit Modal
 */

import React, { useState, useEffect } from 'react';
import { FiX } from 'react-icons/fi';
import { toast } from 'react-toastify';

const UserModal = ({ isOpen, onClose, onSubmit, user, isEdit = false }) => {
  const [formData, setFormData] = useState({
    uid: '',
    cn: '',
    givenName: '',
    sn: '',
    mail: '',
    userPassword: '',
    confirmPassword: '',
    description: '',
    loginShell: '/bin/bash',
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (user && isEdit) {
      setFormData({
        uid: user.uid || '',
        cn: user.cn || '',
        givenName: user.givenName || '',
        sn: user.sn || '',
        mail: user.mail || '',
        description: user.description || '',
        loginShell: user.loginShell || '/bin/bash',
        userPassword: '',
        confirmPassword: '',
      });
    } else {
      setFormData({
        uid: '',
        cn: '',
        givenName: '',
        sn: '',
        mail: '',
        userPassword: '',
        confirmPassword: '',
        description: '',
        loginShell: '/bin/bash',
      });
    }
    setErrors({});
  }, [user, isEdit, isOpen]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validate = () => {
    const newErrors = {};

    if (!formData.uid.trim()) {
      newErrors.uid = 'Username is required';
    } else if (!/^[a-z][a-z0-9._-]*$/.test(formData.uid)) {
      newErrors.uid = 'Username must start with a letter and contain only lowercase letters, numbers, dots, hyphens, and underscores';
    }

    if (!formData.cn.trim()) {
      newErrors.cn = 'Full name is required';
    }

    if (!formData.sn.trim() && !formData.givenName.trim()) {
      newErrors.sn = 'Either last name or first name is required';
    }

    if (formData.mail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.mail)) {
      newErrors.mail = 'Invalid email address';
    }

    if (!isEdit) {
      if (!formData.userPassword) {
        newErrors.userPassword = 'Password is required';
      } else if (formData.userPassword.length < 12) {
        newErrors.userPassword = 'Password must be at least 12 characters';
      } else if (!/[A-Z]/.test(formData.userPassword)) {
        newErrors.userPassword = 'Password must contain at least one uppercase letter';
      } else if (!/[a-z]/.test(formData.userPassword)) {
        newErrors.userPassword = 'Password must contain at least one lowercase letter';
      } else if (!/\d/.test(formData.userPassword)) {
        newErrors.userPassword = 'Password must contain at least one number';
      } else if (!/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(formData.userPassword)) {
        newErrors.userPassword = 'Password must contain at least one special character';
      }

      if (formData.userPassword !== formData.confirmPassword) {
        newErrors.confirmPassword = 'Passwords do not match';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const submitData = { ...formData };
      delete submitData.confirmPassword;

      if (isEdit) {
        // Remove password fields if empty
        if (!submitData.userPassword) {
          delete submitData.userPassword;
        }
        // Remove uid from update
        delete submitData.uid;
      }

      await onSubmit(submitData);
      onClose();
      toast.success(isEdit ? 'User updated successfully' : 'User created successfully');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
          onClick={onClose}
        ></div>

        {/* Modal panel */}
        <div className="inline-block w-full max-w-2xl p-6 my-8 overflow-hidden text-left align-middle transition-all transform bg-white shadow-xl rounded-lg">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              {isEdit ? 'Edit User' : 'Create New User'}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500"
            >
              <FiX className="w-6 h-6" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {/* Username */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Username <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="uid"
                  value={formData.uid}
                  onChange={handleChange}
                  disabled={isEdit}
                  className={`input-field ${errors.uid ? 'border-red-500' : ''} ${isEdit ? 'bg-gray-100' : ''}`}
                />
                {errors.uid && <p className="mt-1 text-sm text-red-600">{errors.uid}</p>}
              </div>

              {/* Full Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="cn"
                  value={formData.cn}
                  onChange={handleChange}
                  className={`input-field ${errors.cn ? 'border-red-500' : ''}`}
                />
                {errors.cn && <p className="mt-1 text-sm text-red-600">{errors.cn}</p>}
              </div>

              {/* First Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  First Name
                </label>
                <input
                  type="text"
                  name="givenName"
                  value={formData.givenName}
                  onChange={handleChange}
                  className="input-field"
                />
              </div>

              {/* Last Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Last Name
                </label>
                <input
                  type="text"
                  name="sn"
                  value={formData.sn}
                  onChange={handleChange}
                  className={`input-field ${errors.sn ? 'border-red-500' : ''}`}
                />
                {errors.sn && <p className="mt-1 text-sm text-red-600">{errors.sn}</p>}
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  name="mail"
                  value={formData.mail}
                  onChange={handleChange}
                  className={`input-field ${errors.mail ? 'border-red-500' : ''}`}
                />
                {errors.mail && <p className="mt-1 text-sm text-red-600">{errors.mail}</p>}
              </div>

              {/* Login Shell */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Login Shell
                </label>
                <select
                  name="loginShell"
                  value={formData.loginShell}
                  onChange={handleChange}
                  className="input-field"
                >
                  <option value="/bin/bash">/bin/bash</option>
                  <option value="/bin/sh">/bin/sh</option>
                  <option value="/bin/zsh">/bin/zsh</option>
                  <option value="/bin/false">/bin/false</option>
                </select>
              </div>

              {/* Password (only for new users or if changing) */}
              {!isEdit && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Password <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="password"
                      name="userPassword"
                      value={formData.userPassword}
                      onChange={handleChange}
                      className={`input-field ${errors.userPassword ? 'border-red-500' : ''}`}
                    />
                    {errors.userPassword && <p className="mt-1 text-sm text-red-600">{errors.userPassword}</p>}
                    <p className="mt-1 text-xs text-gray-500">Min 12 chars, uppercase, lowercase, number, special char</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Confirm Password <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="password"
                      name="confirmPassword"
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      className={`input-field ${errors.confirmPassword ? 'border-red-500' : ''}`}
                    />
                    {errors.confirmPassword && <p className="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>}
                  </div>
                </>
              )}

              {/* Description */}
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows={3}
                  className="input-field"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="btn-secondary"
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn-primary"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Saving...' : isEdit ? 'Update User' : 'Create User'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default UserModal;

