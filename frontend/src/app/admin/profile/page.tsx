'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { API_ENDPOINTS } from '@/config/api';

interface ProfileData {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
  is_email_verified: boolean;
  date_joined: string;
  last_login: string;
}

export default function ProfileSettings() {
  const { user } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [profileData, setProfileData] = useState<ProfileData | null>(null);
  const [originalEmail, setOriginalEmail] = useState('');
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
  });
  const [showEmailVerifyModal, setShowEmailVerifyModal] = useState(false);
  const [showEmailVerificationModal, setShowEmailVerificationModal] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [verificationOtp, setVerificationOtp] = useState('');
  const [otpSending, setOtpSending] = useState(false);
  const [otpVerifying, setOtpVerifying] = useState(false);
  const [verificationSending, setVerificationSending] = useState(false);
  const [verificationVerifying, setVerificationVerifying] = useState(false);
  const [currentEmailMasked, setCurrentEmailMasked] = useState('');
  const [newEmailPending, setNewEmailPending] = useState('');
  const [notification, setNotification] = useState<{
    show: boolean;
    type: 'success' | 'error';
    message: string;
  }>({
    show: false,
    type: 'success',
    message: ''
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(API_ENDPOINTS.admin.profile, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setProfileData(data);
        setOriginalEmail(data.email);
        setFormData({
          first_name: data.first_name || '',
          last_name: data.last_name || '',
          email: data.email || '',
        });
      }
    } catch (error) {
            showNotification('error', 'Failed to load profile data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Check if email changed
    if (formData.email.toLowerCase() !== originalEmail.toLowerCase()) {
      // Request OTP for email change
      setOtpSending(true);
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(API_ENDPOINTS.admin.requestEmailChange, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ new_email: formData.email })
        });

        if (response.ok) {
          const data = await response.json();
          setCurrentEmailMasked(data.current_email_masked);
          setNewEmailPending(formData.email);
          setShowEmailVerifyModal(true);
          showNotification('success', data.message);
        } else {
          const errorData = await response.json();
          showNotification('error', errorData.error || 'Failed to request email change');
          // Reset email to original
          setFormData(prev => ({ ...prev, email: originalEmail }));
        }
      } catch (error) {
                showNotification('error', 'An error occurred while requesting email change');
        setFormData(prev => ({ ...prev, email: originalEmail }));
      } finally {
        setOtpSending(false);
      }
      return;
    }

    // Normal profile update (no email change)
    setSaving(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(API_ENDPOINTS.admin.profile, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          first_name: formData.first_name,
          last_name: formData.last_name,
        })
      });

      if (response.ok) {
        const data = await response.json();
        setProfileData(data);
        showNotification('success', 'Profile updated successfully');
      } else {
        const errorData = await response.json();
        showNotification('error', errorData.error || 'Failed to update profile');
      }
    } catch (error) {
            showNotification('error', 'An error occurred while updating profile');
    } finally {
      setSaving(false);
    }
  };

  const handleVerifyOTP = async () => {
    if (!otpCode || otpCode.length !== 6) {
      showNotification('error', 'Please enter a valid 6-digit code');
      return;
    }

    setOtpVerifying(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(API_ENDPOINTS.admin.verifyEmailChange, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ otp: otpCode })
      });

      if (response.ok) {
        const data = await response.json();
        showNotification('success', 'Email updated successfully!');
        setShowEmailVerifyModal(false);
        setOtpCode('');
        // Refresh profile to get updated email
        await fetchProfile();
      } else {
        const errorData = await response.json();
        showNotification('error', errorData.error || 'Invalid verification code');
      }
    } catch (error) {
            showNotification('error', 'An error occurred while verifying code');
    } finally {
      setOtpVerifying(false);
    }
  };

  const handleCancelEmailChange = () => {
    setShowEmailVerifyModal(false);
    setOtpCode('');
    setFormData(prev => ({ ...prev, email: originalEmail }));
  };

  const handleRequestEmailVerification = async () => {
    setVerificationSending(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(API_ENDPOINTS.admin.requestEmailVerification, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentEmailMasked(data.masked_email || '');
        setShowEmailVerificationModal(true);
        showNotification('success', data.message || 'Verification code sent to your email');
      } else {
        const errorData = await response.json();
        showNotification('error', errorData.error || 'Failed to send verification code');
      }
    } catch (error) {
            showNotification('error', 'An error occurred while sending verification code');
    } finally {
      setVerificationSending(false);
    }
  };

  const handleVerifyEmailOTP = async () => {
    if (!verificationOtp || verificationOtp.length !== 6) {
      showNotification('error', 'Please enter a valid 6-digit code');
      return;
    }

    setVerificationVerifying(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(API_ENDPOINTS.admin.verifyEmail, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ otp: verificationOtp })
      });

      if (response.ok) {
        const data = await response.json();
        showNotification('success', 'Email verified successfully!');
        setShowEmailVerificationModal(false);
        setVerificationOtp('');
        // Refresh profile to update verification status
        await fetchProfile();
      } else {
        const errorData = await response.json();
        showNotification('error', errorData.error || 'Invalid verification code');
      }
    } catch (error) {
            showNotification('error', 'An error occurred while verifying email');
    } finally {
      setVerificationVerifying(false);
    }
  };

  const handleCancelEmailVerification = () => {
    setShowEmailVerificationModal(false);
    setVerificationOtp('');
  };

  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ show: true, type, message });
    setTimeout(() => {
      setNotification({ show: false, type: 'success', message: '' });
    }, 5000);
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="flex items-center gap-3 text-gray-600">
          <div className="animate-spin rounded-full h-6 w-6 border-2 border-gray-300 border-t-[#00B38F]"></div>
          <span className="font-medium">Loading profile...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Notification Toast */}
      {notification.show && (
        <div className="fixed top-4 right-4 z-50 max-w-md">
          <div className={`rounded-lg shadow-lg p-4 ${
            notification.type === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
          }`}>
            <div className="flex items-start">
              <div className="flex-shrink-0">
                {notification.type === 'success' ? (
                  <svg className="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5 text-red-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                  </svg>
                )}
              </div>
              <div className="ml-3">
                <p className={`text-sm font-medium ${
                  notification.type === 'success' ? 'text-green-800' : 'text-red-800'
                }`}>
                  {notification.message}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Profile Settings</h1>
              <p className="text-gray-600 mt-1">Manage your account information</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Profile Summary Card */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="text-center">
                <div className="w-24 h-24 bg-[#00B38F] rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-white text-3xl font-bold">
                    {(formData.first_name || user?.username || 'A').charAt(0).toUpperCase()}
                  </span>
                </div>
                <h2 className="text-xl font-semibold text-gray-900">
                  {formData.first_name} {formData.last_name}
                </h2>
                <p className="text-gray-600 text-sm mt-1">@{profileData?.username}</p>
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-teal-100 text-teal-800 mt-3">
                  Super Admin
                </span>
              </div>

              <div className="mt-6 pt-6 border-t border-gray-200 space-y-4">
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Email Status</p>
                  <div className="mt-1 flex items-center gap-2">
                    {profileData?.is_email_verified ? (
                      <>
                        <svg className="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="text-sm text-gray-900">Verified</span>
                      </>
                    ) : (
                      <>
                        <svg className="h-4 w-4 text-amber-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                        </svg>
                        <span className="text-sm text-gray-900">Not Verified</span>
                      </>
                    )}
                  </div>
                </div>

                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Account Created</p>
                  <p className="text-sm text-gray-900 mt-1">{formatDate(profileData?.date_joined || '')}</p>
                </div>

                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Last Login</p>
                  <p className="text-sm text-gray-900 mt-1">{formatDate(profileData?.last_login || '')}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Profile Form */}
          <div className="lg:col-span-2">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Personal Information */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Personal Information</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-1">
                      First Name
                    </label>
                    <input
                      type="text"
                      id="first_name"
                      value={formData.first_name}
                      onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-[#00B38F] focus:border-transparent"
                      placeholder="Enter first name"
                    />
                  </div>

                  <div>
                    <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-1">
                      Last Name
                    </label>
                    <input
                      type="text"
                      id="last_name"
                      value={formData.last_name}
                      onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-[#00B38F] focus:border-transparent"
                      placeholder="Enter last name"
                    />
                  </div>
                </div>

                <div className="mt-4">
                  <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                    Username
                  </label>
                  <input
                    type="text"
                    id="username"
                    value={profileData?.username || ''}
                    disabled
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500 cursor-not-allowed"
                  />
                  <p className="text-xs text-gray-500 mt-1">Username cannot be changed</p>
                </div>
              </div>

              {/* Contact Information */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h3>
                
                <div className="space-y-4">
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                      Email Address
                    </label>
                    <div className="relative">
                      <input
                        type="email"
                        id="email"
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-[#00B38F] focus:border-transparent"
                        placeholder="admin@example.com"
                      />
                      {profileData?.is_email_verified && (
                        <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                          <svg className="h-5 w-5 text-green-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </div>
                      )}
                    </div>
                    {!profileData?.is_email_verified && (
                      <div className="mt-2 flex items-center justify-between bg-amber-50 border border-amber-200 rounded-md p-3">
                        <div className="flex items-center gap-2">
                          <svg className="h-5 w-5 text-amber-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                          </svg>
                          <span className="text-sm text-amber-800 font-medium">Email not verified</span>
                        </div>
                        <button
                          type="button"
                          onClick={handleRequestEmailVerification}
                          disabled={verificationSending}
                          className="inline-flex items-center px-4 py-1.5 bg-[#00B38F] text-white text-sm font-medium rounded-md hover:bg-[#009975] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#00B38F] disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {verificationSending ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                              Sending...
                            </>
                          ) : (
                            <>
                              <svg className="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              Verify Now
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => router.push('/admin/change-password')}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                  </svg>
                  Change Password
                </button>

                <button
                  type="submit"
                  disabled={saving}
                  className="inline-flex items-center px-6 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-[#00B38F] hover:bg-[#009975] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#00B38F] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saving ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                      Saving...
                    </>
                  ) : (
                    <>
                      <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                      </svg>
                      Save Changes
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Email Verification OTP Modal */}
      {showEmailVerifyModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            {/* Background overlay */}
            <div 
              className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
              onClick={handleCancelEmailChange}
            />

            {/* Modal panel */}
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 sm:mx-0 sm:h-10 sm:w-10">
                    <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
                    </svg>
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left flex-1">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Verify Email Change
                    </h3>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500">
                        For security, we've sent a verification code to your current email address:
                      </p>
                      <p className="text-sm font-medium text-gray-900 mt-1">
                        {currentEmailMasked}
                      </p>
                      <p className="text-sm text-gray-500 mt-3">
                        Please enter the 6-digit code to change your email to:
                      </p>
                      <p className="text-sm font-medium text-[#00B38F] mt-1">
                        {newEmailPending}
                      </p>
                    </div>

                    <div className="mt-4">
                      <label htmlFor="otp" className="block text-sm font-medium text-gray-700 mb-2">
                        Verification Code
                      </label>
                      <input
                        type="text"
                        id="otp"
                        maxLength={6}
                        value={otpCode}
                        onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                        className="w-full px-4 py-3 text-center text-2xl font-mono tracking-widest border border-gray-300 rounded-md text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-[#00B38F] focus:border-transparent"
                        placeholder="000000"
                        autoFocus
                      />
                      <p className="text-xs text-gray-500 mt-2">
                        Code expires in 10 minutes
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse gap-2">
                <button
                  type="button"
                  onClick={handleVerifyOTP}
                  disabled={otpVerifying || otpCode.length !== 6}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-[#00B38F] text-base font-medium text-white hover:bg-[#009975] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#00B38F] sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {otpVerifying ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                      Verifying...
                    </>
                  ) : (
                    'Verify & Update Email'
                  )}
                </button>
                <button
                  type="button"
                  onClick={handleCancelEmailChange}
                  disabled={otpVerifying}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#00B38F] sm:mt-0 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Email Verification Modal */}
      {showEmailVerificationModal && (
        <div className="fixed z-50 inset-0 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            {/* Background overlay */}
            <div 
              className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
              onClick={handleCancelEmailVerification}
            />

            {/* Modal panel */}
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-[#00B38F]/10 sm:mx-0 sm:h-10 sm:w-10">
                    <svg className="h-6 w-6 text-[#00B38F]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left flex-1">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Verify Your Email
                    </h3>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500">
                        We've sent a verification code to:
                      </p>
                      <p className="text-sm font-medium text-gray-900 mt-1">
                        {currentEmailMasked || formData.email}
                      </p>
                      <p className="text-sm text-gray-500 mt-3">
                        Please enter the 6-digit code to verify your email address.
                      </p>
                    </div>

                    <div className="mt-4">
                      <label htmlFor="verification-otp" className="block text-sm font-medium text-gray-700 mb-2">
                        Verification Code
                      </label>
                      <input
                        type="text"
                        id="verification-otp"
                        maxLength={6}
                        value={verificationOtp}
                        onChange={(e) => setVerificationOtp(e.target.value.replace(/\D/g, ''))}
                        className="w-full px-4 py-3 text-center text-2xl font-mono tracking-widest border border-gray-300 rounded-md text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-[#00B38F] focus:border-transparent"
                        placeholder="000000"
                        autoFocus
                      />
                      <p className="text-xs text-gray-500 mt-2">
                        Code expires in 10 minutes
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse gap-2">
                <button
                  type="button"
                  onClick={handleVerifyEmailOTP}
                  disabled={verificationVerifying || verificationOtp.length !== 6}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-[#00B38F] text-base font-medium text-white hover:bg-[#009975] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#00B38F] sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {verificationVerifying ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                      Verifying...
                    </>
                  ) : (
                    'Verify Email'
                  )}
                </button>
                <button
                  type="button"
                  onClick={handleCancelEmailVerification}
                  disabled={verificationVerifying}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#00B38F] sm:mt-0 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
