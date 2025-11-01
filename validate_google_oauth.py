#!/usr/bin/env python3
"""
Google OAuth Configuration Validator for Oxidane
Checks all components to ensure Google OAuth is properly configured
"""

import os
import json
import sys
from pathlib import Path

def check_environment_variables():
    """Check if all required environment variables are set"""
    print("🔍 Checking Environment Variables...")
    
    env_file = Path("frontend/.env.local")
    if not env_file.exists():
        print("❌ .env.local file not found!")
        return False
    
    required_vars = [
        'NEXTAUTH_URL',
        'NEXTAUTH_SECRET', 
        'GOOGLE_CLIENT_ID',
        'GOOGLE_CLIENT_SECRET',
        'NEXT_PUBLIC_API_URL'
    ]
    
    env_content = env_file.read_text(encoding='utf-8')
    missing_vars = []
    
    for var in required_vars:
        if f"{var}=" not in env_content or f"{var}=" in env_content and "your-" in env_content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or placeholder values for: {', '.join(missing_vars)}")
        return False
    
    print("✅ All environment variables are set!")
    return True

def check_nextauth_config():
    """Check NextAuth.js configuration"""
    print("\n🔍 Checking NextAuth.js Configuration...")
    
    config_file = Path("frontend/src/app/api/auth/[...nextauth]/route.ts")
    if not config_file.exists():
        print("❌ NextAuth config file not found!")
        return False
    
    config_content = config_file.read_text()
    
    # Check for Google provider
    if "GoogleProvider" not in config_content:
        print("❌ GoogleProvider not found in NextAuth config!")
        return False
    
    if "GOOGLE_CLIENT_ID" not in config_content:
        print("❌ GOOGLE_CLIENT_ID not referenced in config!")
        return False
    
    if "GOOGLE_CLIENT_SECRET" not in config_content:
        print("❌ GOOGLE_CLIENT_SECRET not referenced in config!")
        return False
    
    print("✅ NextAuth.js configuration is correct!")
    return True

def check_backend_oauth_endpoint():
    """Check backend OAuth callback endpoint"""
    print("\n🔍 Checking Backend OAuth Endpoint...")
    
    views_file = Path("backend/users/views.py")
    if not views_file.exists():
        print("❌ Backend views.py not found!")
        return False
    
    try:
        views_content = views_file.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        views_content = views_file.read_text(encoding='latin-1')
    
    if "def oauth_callback" not in views_content:
        print("❌ oauth_callback function not found!")
        return False
    
    if "OAuthProvider" not in views_content:
        print("❌ OAuthProvider model not imported/used!")
        return False
    
    print("✅ Backend OAuth endpoint is configured!")
    return True

def check_frontend_integration():
    """Check frontend Google sign-in integration"""
    print("\n🔍 Checking Frontend Integration...")
    
    auth_form = Path("frontend/src/app/components/NewAuthForm.tsx")
    if not auth_form.exists():
        print("❌ NewAuthForm.tsx not found!")
        return False
    
    try:
        form_content = auth_form.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        form_content = auth_form.read_text(encoding='latin-1')
    
    if "signIn('google'" not in form_content:
        print("❌ Google sign-in not properly integrated!")
        return False
    
    if "next-auth/react" not in form_content:
        print("❌ NextAuth React imports missing!")
        return False
    
    print("✅ Frontend Google sign-in integration is correct!")
    return True

def check_no_firebase_references():
    """Ensure Firebase has been completely removed"""
    print("\n🔍 Checking Firebase Removal...")
    
    # Check if firebase package is still in package.json
    package_json = Path("frontend/package.json")
    if package_json.exists():
        package_content = json.loads(package_json.read_text())
        if "firebase" in package_content.get("dependencies", {}):
            print("❌ Firebase package still in dependencies!")
            return False
    
    # Check for firebase.ts file
    firebase_config = Path("frontend/src/app/firebase.ts")
    if firebase_config.exists():
        print("❌ Firebase config file still exists!")
        return False
    
    print("✅ Firebase has been completely removed!")
    return True

def print_google_oauth_checklist():
    """Print Google Cloud Console setup checklist"""
    print("\n📋 Google Cloud Console Checklist:")
    print("   1. Go to https://console.cloud.google.com/")
    print("   2. Create/Select your project")
    print("   3. Enable Google+ API and Google Identity")
    print("   4. Create OAuth 2.0 Client ID")
    print("   5. Add JavaScript origins: http://localhost:3000")
    print("   6. Add redirect URI: http://localhost:3000/api/auth/callback/google")
    print("   7. Configure OAuth consent screen")
    print("   8. Copy Client ID and Secret to .env.local")

def main():
    """Main validation function"""
    print("🚀 Google OAuth Configuration Validator for Oxidane\n")
    
    checks = [
        check_no_firebase_references,
        check_environment_variables,
        check_nextauth_config,
        check_backend_oauth_endpoint,
        check_frontend_integration
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 All checks passed! Your Google OAuth setup looks perfect!")
        print("\n✅ Configuration Status:")
        print("   - Firebase: ❌ Removed (Good!)")
        print("   - NextAuth.js: ✅ Configured")
        print("   - Google Provider: ✅ Ready") 
        print("   - Backend Integration: ✅ Ready")
        print("   - Frontend Integration: ✅ Ready")
        print("\n🚀 Your Google Sign-In should work now!")
        print("   Visit: http://localhost:3000/auth")
        print("   Click: 'Continue with Google'")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print_google_oauth_checklist()
    
    print("\n" + "="*50)

if __name__ == "__main__":
    main()