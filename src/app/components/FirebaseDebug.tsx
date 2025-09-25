'use client';

import { useState } from 'react';
import { auth } from '../firebase';

export default function FirebaseDebug() {
  const [testResult, setTestResult] = useState('');
  const [connectivityResult, setConnectivityResult] = useState('');

  const testFirebaseConnection = () => {
    setTestResult('Testing Firebase connection...');
    
    try {
      // Test if auth is initialized
      if (!auth) {
        setTestResult('❌ Firebase auth not initialized');
        return;
      }

      if (!auth.app) {
        setTestResult('❌ Firebase app not found');
        return;
      }

      // Check config
      const config = auth.app.options;
      const configStatus = {
        apiKey: config.apiKey ? '✅' : '❌',
        authDomain: config.authDomain ? '✅' : '❌',
        projectId: config.projectId ? '✅' : '❌',
      };

      setTestResult(`
        Firebase Status:
        Auth initialized: ✅
        API Key: ${configStatus.apiKey}
        Auth Domain: ${configStatus.authDomain}
        Project ID: ${configStatus.projectId}
        
        Config Details:
        Auth Domain: ${config.authDomain}
        Project ID: ${config.projectId}
      `);

    } catch (error) {
      setTestResult(`❌ Error: ${error}`);
    }
  };

  const testConnectivity = async () => {
    setConnectivityResult('Testing connectivity...');
    
    const domains = [
      'https://firebase.googleapis.com',
      'https://identitytoolkit.googleapis.com',
      'https://accounts.google.com',
      'https://oxidane-dd474.firebaseapp.com',
      'https://oxidane-dd474.web.app'
    ];

    const results = [];

    for (const domain of domains) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch(domain + '/favicon.ico', {
          method: 'HEAD',
          signal: controller.signal,
          mode: 'no-cors'
        });
        
        clearTimeout(timeoutId);
        results.push(`✅ ${domain} - Reachable`);
      } catch (error: any) {
        if (error.name === 'AbortError') {
          results.push(`⏱️ ${domain} - Timeout`);
        } else {
          results.push(`❌ ${domain} - Error: ${error.message}`);
        }
      }
    }

    setConnectivityResult(results.join('\n'));
  };

  const fixAuthDomain = () => {
    const newConfig = `
To fix the auth domain issue, try these steps:

1. In Firebase Console → Authentication → Settings → Authorized domains:
   - Add: localhost
   - Add: 127.0.0.1
   - Add: your-actual-domain.com

2. Alternative auth domain options:
   - Try: oxidane-dd474.web.app instead of .firebaseapp.com
   - Or use: ${auth.app.options.projectId}.firebaseapp.com

3. For local development, you can also use:
   - Auth domain: localhost:3000 (add to authorized domains)

Click "Test Alternative Domain" to try the .web.app domain.
    `;
    
    setConnectivityResult(newConfig);
  };

  const testAlternativeDomain = async () => {
    try {
      // This would require updating the Firebase config, but let's test connectivity first
      const altDomain = 'https://oxidane-dd474.web.app';
      
      setConnectivityResult('Testing alternative domain...');
      
      const response = await fetch(altDomain, { 
        method: 'HEAD', 
        mode: 'no-cors',
        signal: AbortSignal.timeout(10000)
      });
      
      setConnectivityResult(`✅ Alternative domain ${altDomain} is reachable!
      
To use this domain:
1. Update your .env.local file:
   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=oxidane-dd474.web.app
2. Restart your dev server
3. Try authentication again`);
      
    } catch (error: any) {
      setConnectivityResult(`❌ Alternative domain test failed: ${error.message}
      
This suggests a broader connectivity issue. Try:
1. Check your internet connection
2. Disable VPN if using one
3. Try a different network
4. Check firewall settings`);
    }
  };

  return (
    <div className="mt-8 p-4 bg-gray-100 rounded-lg">
      <h3 className="text-lg font-semibold mb-4">Firebase Debug & Connectivity</h3>
      
      <div className="space-y-2 mb-4">
        <button
          onClick={testFirebaseConnection}
          className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 mr-2"
        >
          Test Firebase Config
        </button>
        
        <button
          onClick={testConnectivity}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 mr-2"
        >
          Test Connectivity
        </button>
        
        <button
          onClick={testAlternativeDomain}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 mr-2"
        >
          Test Alternative Domain
        </button>
        
        <button
          onClick={fixAuthDomain}
          className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700"
        >
          Fix Auth Domain
        </button>
      </div>

      {testResult && (
        <div className="mb-4">
          <h4 className="font-semibold mb-2">Firebase Config Test:</h4>
          <pre className="bg-white p-3 rounded border text-sm whitespace-pre-wrap">
            {testResult}
          </pre>
        </div>
      )}

      {connectivityResult && (
        <div>
          <h4 className="font-semibold mb-2">Connectivity Test:</h4>
          <pre className="bg-white p-3 rounded border text-sm whitespace-pre-wrap">
            {connectivityResult}
          </pre>
        </div>
      )}
    </div>
  );
}