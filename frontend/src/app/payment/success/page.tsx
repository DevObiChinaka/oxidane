'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useUserAuth } from '../../contexts/UserAuthContext';
import Navigation from '../../components/Navigation';
import Footer from '../../components/Footer';

function SuccessContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user } = useUserAuth();
  const reference = searchParams.get('reference');
  
  const [countdown, setCountdown] = useState(10);
  const [subscription, setSubscription] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Fetch subscription details
  useEffect(() => {
    const fetchSubscription = async () => {
      try {
        const token = localStorage.getItem('user_auth_token');
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/subscriptions/my-subscriptions/`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        );

        if (response.ok) {
          const data = await response.json();
          // Get the most recent subscription (first in array)
          if (data.subscriptions && data.subscriptions.length > 0) {
            setSubscription(data.subscriptions[0]);
          }
        }
      } catch (err) {
        console.error('Failed to fetch subscription:', err);
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      fetchSubscription();
    }
  }, [user]);

  // Countdown to dashboard redirect
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Redirect when countdown reaches 0
  useEffect(() => {
    if (countdown <= 0) {
      router.push('/dashboard');
    }
  }, [countdown, router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#000856] via-[#002A5C] to-[#004A42]">
      <Navigation />
      
      {/* Background Elements */}
      <div className="absolute inset-0 opacity-8">
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.08'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }}></div>
      </div>

      {/* Confetti Effect */}
      <div className="absolute inset-0 pointer-events-none">
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            className="absolute w-2 h-2 bg-[#00B38F] rounded-full animate-ping"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 2}s`,
              animationDuration: `${2 + Math.random() * 2}s`
            }}
          />
        ))}
      </div>

      <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-12">
          {/* Success Icon */}
          <div className="inline-flex items-center justify-center w-24 h-24 bg-green-500/20 rounded-full mb-6 animate-bounce">
            <svg className="w-12 h-12 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>

          {/* Success Message */}
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            {subscription?.is_trial ? 'Trial Started! 🎉' : 'Payment Successful! 🎉'}
          </h1>
          <p className="text-xl text-gray-300 mb-2">
            Welcome to the premium experience, {user?.first_name || 'Trader'}!
          </p>
          {subscription?.is_trial ? (
            <p className="text-gray-400">
              Your {subscription.days_until_trial_end}-day free trial is now active
            </p>
          ) : (
            <p className="text-gray-400">
              Your subscription is now active and ready to use
            </p>
          )}
        </div>

        {/* Success Details Card */}
        <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-8 mb-8">
          <div className="grid md:grid-cols-2 gap-8">
            {/* Left Column */}
            <div>
              <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                <svg className="w-6 h-6 text-[#00B38F]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                What's Next?
              </h2>

              <div className="space-y-4">
                {subscription?.is_trial && (
                  <div className="bg-[#000ABE]/20 border border-[#000ABE]/30 rounded-lg p-4 mb-6">
                    <div className="flex items-start gap-3">
                      <svg className="w-5 h-5 text-[#00B38F] flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <div>
                        <h4 className="text-white font-semibold text-sm mb-1">
                          Free Trial Active - {subscription.days_until_trial_end} Days Remaining
                        </h4>
                        <p className="text-gray-300 text-xs leading-relaxed">
                          Your trial ends on {new Date(subscription.trial_end_date).toLocaleDateString('en-US', { 
                            month: 'long', 
                            day: 'numeric', 
                            year: 'numeric' 
                          })}. 
                          {' '}After that, you'll be charged {subscription.currency} {subscription.plan_base_price.toFixed(2)} automatically unless you cancel.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-[#00B38F]/20 rounded-full flex items-center justify-center text-[#00B38F] font-bold text-sm">
                    1
                  </div>
                  <div>
                    <h3 className="text-white font-medium mb-1">Check Your Email</h3>
                    <p className="text-gray-300 text-sm">
                      We've sent a {subscription?.is_trial ? 'trial confirmation' : 'receipt'} and welcome email to {user?.email}
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-[#00B38F]/20 rounded-full flex items-center justify-center text-[#00B38F] font-bold text-sm">
                    2
                  </div>
                  <div>
                    <h3 className="text-white font-medium mb-1">Join Telegram Groups</h3>
                    <p className="text-gray-300 text-sm">
                      You'll receive Telegram group invites within 1-2 minutes
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-[#00B38F]/20 rounded-full flex items-center justify-center text-[#00B38F] font-bold text-sm">
                    3
                  </div>
                  <div>
                    <h3 className="text-white font-medium mb-1">Access Your Dashboard</h3>
                    <p className="text-gray-300 text-sm">
                      View signals, courses, and manage your subscription
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column */}
            <div>
              <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                <svg className="w-6 h-6 text-[#00B38F]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Payment Details
              </h2>

              <div className="bg-white/5 rounded-lg p-4 space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Reference</span>
                  <span className="text-white font-mono">{reference || 'N/A'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Status</span>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-500/20 text-green-400">
                    Completed
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Date</span>
                  <span className="text-white">{new Date().toLocaleDateString()}</span>
                </div>
              </div>

              {/* TODO: Implement invoice download once backend PDF generation is complete */}
              {false && (
                <button
                  className="w-full mt-4 px-6 py-3 bg-white/10 border border-white/20 text-white rounded-lg hover:bg-white/20 transition-colors font-medium"
                >
                  <span className="flex items-center justify-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Download Invoice
                  </span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Auto-redirect Countdown Banner */}
        {countdown > 0 && (
          <div className="bg-[#00B38F]/20 border border-[#00B38F]/30 rounded-xl p-4 mb-8 animate-pulse">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <svg className="w-8 h-8 text-[#00B38F]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-[#00B38F] font-bold text-xs">{countdown}</span>
                  </div>
                </div>
                <div>
                  <p className="text-white font-medium">
                    Redirecting to dashboard in {countdown} second{countdown !== 1 ? 's' : ''}...
                  </p>
                  <p className="text-gray-300 text-sm">
                    Or click the button below to go now
                  </p>
                </div>
              </div>
              <button
                onClick={() => setCountdown(0)}
                className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Skip
              </button>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="grid sm:grid-cols-2 gap-4 mb-8">
          <button
            onClick={() => router.push('/dashboard')}
            className="px-8 py-4 bg-gradient-to-r from-[#00B38F] to-[#00B39F] text-white rounded-xl font-semibold text-lg hover:opacity-90 transition-opacity"
          >
            Go to Dashboard
          </button>
          <button
            onClick={() => router.push('/courses')}
            className="px-8 py-4 bg-white/10 border border-white/20 text-white rounded-xl font-semibold text-lg hover:bg-white/20 transition-colors"
          >
            Browse Courses
          </button>
        </div>

        {/* Auto-redirect Notice */}
        <div className="text-center">
          <p className="text-gray-400 text-sm">
            Automatically redirecting to dashboard in {countdown} seconds...
          </p>
        </div>

        {/* Support */}
        <div className="mt-12 text-center">
          <p className="text-gray-400 text-sm mb-2">
            Need help? Our support team is here for you 24/7
          </p>
          <a
            href="/support"
            className="text-[#00B38F] hover:text-[#00A87D] text-sm font-medium"
          >
            Contact Support →
          </a>
        </div>
      </div>

      <Footer />
    </div>
  );
}

export default function PaymentSuccessPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-[#000856] via-[#002A5C] to-[#004A42] flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-2 border-[#00B38F] mb-4"></div>
          <p className="text-white text-lg">Loading...</p>
        </div>
      </div>
    }>
      <SuccessContent />
    </Suspense>
  );
}
