'use client';

import { useState } from 'react';

export default function DomainTester() {
  const [currentDomain, setCurrentDomain] = useState('');

  const checkCurrentDomain = () => {
    if (typeof window !== 'undefined') {
      const info = {
        hostname: window.location.hostname,
        port: window.location.port,
        protocol: window.location.protocol,
        origin: window.location.origin,
        href: window.location.href,
      };
      
      setCurrentDomain(`
Current Domain Info:
- Hostname: ${info.hostname}
- Port: ${info.port}
- Protocol: ${info.protocol}
- Origin: ${info.origin}
- Full URL: ${info.href}

Add to Firebase Authorized Domains:
✅ ${info.hostname} (primary)
✅ 127.0.0.1 (alternative)
✅ ${info.origin} (if above don't work)
      `);
    }
  };

  return (
    <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
      <h4 className="font-semibold text-yellow-800 mb-2">Domain Checker</h4>
      
      <button
        onClick={checkCurrentDomain}
        className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 mb-3"
      >
        Check Current Domain
      </button>

      {currentDomain && (
        <pre className="bg-white p-3 rounded border text-sm whitespace-pre-wrap text-gray-800">
          {currentDomain}
        </pre>
      )}
      
      <div className="mt-3 text-sm text-yellow-700">
        <p><strong>Tip:</strong> Copy the hostname from above and paste it in Firebase Console → Authentication → Settings → Authorized domains</p>
      </div>
    </div>
  );
}