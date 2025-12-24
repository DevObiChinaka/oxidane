'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { verifyPayment } from '@/lib/api/payment';

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'verifying' | 'success' | 'failed'>('verifying');
  const [message, setMessage] = useState('Verifying your payment...');

  useEffect(() => {
    const verify = async () => {
      const reference = searchParams.get('reference');
      
      if (!reference) {
        setStatus('failed');
        setMessage('Invalid payment reference');
        setTimeout(() => router.push('/payment/failed'), 2000);
        return;
      }

      try {
        const data = await verifyPayment({ reference });

        if (data.success) {
          setStatus('success');
          setMessage('Payment verified successfully!');
          
          // Redirect to success page after 2 seconds
          setTimeout(() => {
            router.push(`/payment/success?reference=${reference}`);
          }, 2000);
        } else {
          throw new Error(data.message || 'Payment verification failed');
        }
      } catch (err) {
                setStatus('failed');
        setMessage(err instanceof Error ? err.message : 'Payment verification failed');
        
        // Redirect to failed page after 2 seconds
        setTimeout(() => {
          router.push(`/payment/failed?reference=${reference}`);
        }, 2000);
      }
    };

    verify();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#000856] via-[#002A5C] to-[#004A42] flex items-center justify-center">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-8 text-center">
          {status === 'verifying' && (
            <>
              <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-4 border-[#00B38F] mb-6"></div>
              <h2 className="text-2xl font-bold text-white mb-2">Verifying Payment</h2>
              <p className="text-gray-300">{message}</p>
              <div className="mt-6 flex items-center justify-center gap-2 text-sm text-gray-400">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <span>Please wait while we confirm your payment...</span>
              </div>
            </>
          )}

          {status === 'success' && (
            <>
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-500/20 rounded-full mb-6">
                <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Payment Verified!</h2>
              <p className="text-gray-300">{message}</p>
              <p className="text-sm text-gray-400 mt-4">Redirecting to success page...</p>
            </>
          )}

          {status === 'failed' && (
            <>
              <div className="inline-flex items-center justify-center w-16 h-16 bg-red-500/20 rounded-full mb-6">
                <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Verification Failed</h2>
              <p className="text-gray-300">{message}</p>
              <p className="text-sm text-gray-400 mt-4">Redirecting...</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function PaymentCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-[#000856] via-[#002A5C] to-[#004A42] flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-2 border-[#00B38F] mb-4"></div>
          <p className="text-white text-lg">Loading...</p>
        </div>
      </div>
    }>
      <CallbackContent />
    </Suspense>
  );
}
