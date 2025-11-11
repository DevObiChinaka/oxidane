'use client';

import { Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Navigation from '../../components/Navigation';
import Footer from '../../components/Footer';

function FailedContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const reference = searchParams.get('reference');

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#000856] via-[#002A5C] to-[#004A42]">
      <Navigation />
      
      {/* Background Elements */}
      <div className="absolute inset-0 opacity-8">
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.08'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }}></div>
      </div>

      <div className="relative z-10 max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-12">
          {/* Error Icon */}
          <div className="inline-flex items-center justify-center w-24 h-24 bg-red-500/20 rounded-full mb-6">
            <svg className="w-12 h-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>

          {/* Error Message */}
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Payment Failed
          </h1>
          <p className="text-xl text-gray-300 mb-2">
            We couldn't process your payment
          </p>
          <p className="text-gray-400">
            Don't worry, no charges were made to your account
          </p>
        </div>

        {/* Error Details Card */}
        <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-red-500/20 p-8 mb-8">
          <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
            <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Common Reasons for Payment Failure
          </h2>

          <div className="space-y-4">
            <div className="flex items-start gap-3 p-4 bg-white/5 rounded-lg">
              <svg className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
              <div>
                <h3 className="text-white font-medium mb-1">Insufficient Funds</h3>
                <p className="text-gray-300 text-sm">
                  Your card or account doesn't have enough balance
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 bg-white/5 rounded-lg">
              <svg className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <div>
                <h3 className="text-white font-medium mb-1">Card Declined</h3>
                <p className="text-gray-300 text-sm">
                  Your bank or card issuer declined the transaction
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 bg-white/5 rounded-lg">
              <svg className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <div>
                <h3 className="text-white font-medium mb-1">Expired Card</h3>
                <p className="text-gray-300 text-sm">
                  The payment card has expired
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 bg-white/5 rounded-lg">
              <svg className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <div>
                <h3 className="text-white font-medium mb-1">Incorrect Details</h3>
                <p className="text-gray-300 text-sm">
                  Card number, CVV, or billing information is incorrect
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 bg-white/5 rounded-lg">
              <svg className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
              </svg>
              <div>
                <h3 className="text-white font-medium mb-1">Network Issues</h3>
                <p className="text-gray-300 text-sm">
                  Connection timeout or network error during payment
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Payment Reference */}
        {reference && (
          <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6 mb-8">
            <h3 className="text-white font-medium mb-2">Transaction Reference</h3>
            <p className="text-gray-300 font-mono text-sm break-all">{reference}</p>
            <p className="text-xs text-gray-400 mt-2">
              Save this reference for support inquiries
            </p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="grid sm:grid-cols-2 gap-4 mb-8">
          <button
            onClick={() => router.push('/pricing')}
            className="px-8 py-4 bg-gradient-to-r from-[#00B38F] to-[#00B39F] text-white rounded-xl font-semibold text-lg hover:opacity-90 transition-opacity"
          >
            Try Again
          </button>
          <button
            onClick={() => router.push('/support')}
            className="px-8 py-4 bg-white/10 border border-white/20 text-white rounded-xl font-semibold text-lg hover:bg-white/20 transition-colors"
          >
            Contact Support
          </button>
        </div>

        {/* Help Section */}
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0">
              <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 className="text-white font-semibold mb-2">Need Help?</h3>
              <p className="text-gray-300 text-sm mb-4">
                Our support team is available 24/7 to assist you with payment issues.
                We'll help you resolve this quickly.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 text-sm">
                <a
                  href="mailto:support@oxiworld.com"
                  className="flex items-center gap-2 text-[#00B38F] hover:text-[#00A87D]"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  support@oxiworld.com
                </a>
                <a
                  href="https://t.me/oxiworld_support"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-[#00B38F] hover:text-[#00A87D]"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295-.002 0-.003 0-.005 0l.213-3.054 5.56-5.022c.24-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.64-.203-.658-.64.135-.954l11.566-4.458c.538-.196 1.006.128.832.941z"/>
                  </svg>
                  Telegram Support
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Alternative Payment Methods */}
        <div className="mt-8 text-center">
          <p className="text-gray-400 text-sm mb-4">
            Having issues with your payment method?
          </p>
          <p className="text-gray-300 text-sm">
            We accept multiple payment methods including cards, bank transfers, and mobile money.
            <br />
            <a href="/pricing" className="text-[#00B38F] hover:text-[#00A87D] font-medium">
              Try a different payment method →
            </a>
          </p>
        </div>
      </div>

      <Footer />
    </div>
  );
}

export default function PaymentFailedPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-[#000856] via-[#002A5C] to-[#004A42] flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-2 border-[#00B38F] mb-4"></div>
          <p className="text-white text-lg">Loading...</p>
        </div>
      </div>
    }>
      <FailedContent />
    </Suspense>
  );
}
