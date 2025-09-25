// lib/firebase.ts
import { initializeApp } from "firebase/app";
import { getAuth, connectAuthEmulator } from "firebase/auth";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);

// Debug information for development
if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
  console.log('🔧 Firebase initialized');
  console.log('🔧 Config validation:');
  console.log('  ✓ API Key:', firebaseConfig.apiKey ? '✓ Present' : '❌ Missing');
  console.log('  ✓ Auth Domain:', firebaseConfig.authDomain || '❌ Missing');
  console.log('  ✓ Project ID:', firebaseConfig.projectId || '❌ Missing');
  console.log('  ✓ App ID:', firebaseConfig.appId ? '✓ Present' : '❌ Missing');
  
  // Validate Firebase configuration
  const requiredFields = ['apiKey', 'authDomain', 'projectId', 'appId'];
  const missingFields = requiredFields.filter(field => !firebaseConfig[field as keyof typeof firebaseConfig]);
  
  if (missingFields.length > 0) {
    console.error('❌ Missing required Firebase config fields:', missingFields);
  } else {
    console.log('✅ All required Firebase config fields present');
    console.log('🌐 Note: Auth domain timeout is normal - Firebase Auth works independently');
  }
}
