import { auth } from "./firebase";
import { 
  createUserWithEmailAndPassword, 
  signInWithEmailAndPassword, 
  signInWithPopup, 
  signInWithRedirect,
  getRedirectResult,
  GoogleAuthProvider,
  signOut,
  onAuthStateChanged,
  User
} from "firebase/auth";

const googleProvider = new GoogleAuthProvider();
// Add additional scopes if needed
googleProvider.addScope('profile');
googleProvider.addScope('email');

// Set custom parameters to avoid issues with domains
googleProvider.setCustomParameters({
  prompt: 'select_account'
});

export async function signup(email: string, password: string) {
  const userCredential = await createUserWithEmailAndPassword(auth, email, password);
  return userCredential.user;
}

export async function login(email: string, password: string) {
  const userCredential = await signInWithEmailAndPassword(auth, email, password);
  return userCredential.user;
}

export async function signInWithGoogle() {
  try {
    console.log('🔄 Starting Google sign-in process...');
    console.log('🔧 Auth object:', auth);
    console.log('🔧 Provider config:', googleProvider);
    console.log('🔧 Auth domain:', auth.app.options.authDomain);
    
    // Try popup method first
    console.log('📱 Attempting popup sign-in...');
    const result = await signInWithPopup(auth, googleProvider);
    console.log('✅ Google sign-in successful:', result.user.email);
    return result.user;
    
  } catch (error: any) {
    console.error('❌ Google sign-in failed with error:', error);
    console.error('❌ Error code:', error.code);
    console.error('❌ Error message:', error.message);
    console.error('❌ Full error object:', error);
    
    // Log specific common Firebase Auth errors
    if (error.code === 'auth/popup-blocked') {
      console.log('🚫 Popup was blocked by browser, trying redirect...');
      try {
        await signInWithRedirect(auth, googleProvider);
        return null; // Result will be handled by getRedirectResult on return
      } catch (redirectError: any) {
        console.error('❌ Redirect also failed:', redirectError);
        throw new Error(`Both popup and redirect failed. ${redirectError.message}`);
      }
    }
    
    if (error.code === 'auth/network-request-failed') {
      throw new Error('Network error. Please check your internet connection and try again.');
    }
    
    if (error.code === 'auth/unauthorized-domain') {
      throw new Error('This domain is not authorized for OAuth operations. Please check your Firebase Console authorized domains.');
    }
    
    if (error.code === 'auth/operation-not-allowed') {
      throw new Error('Google sign-in is not enabled. Please enable it in your Firebase Console.');
    }
    
    if (error.code === 'auth/invalid-api-key') {
      throw new Error('Invalid Firebase API key. Please check your configuration.');
    }
    
    throw new Error(`Authentication failed: ${error.code} - ${error.message}`);
  }
}

export async function handleRedirectResult() {
  try {
    console.log('Checking for redirect result...');
    const result = await getRedirectResult(auth);
    if (result) {
      console.log('Redirect result found:', result.user);
    }
    return result?.user || null;
  } catch (error) {
    console.error('Redirect result error:', error);
    return null;
  }
}

export async function logout() {
  await signOut(auth);
}

export function onAuthChange(callback: (user: User | null) => void) {
  return onAuthStateChanged(auth, callback);
}
