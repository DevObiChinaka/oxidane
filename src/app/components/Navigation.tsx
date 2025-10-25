'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useSession } from 'next-auth/react';
import Image from 'next/image';

export default function Navigation() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { data: session } = useSession();

  return (
    <nav className="bg-[#000856]/90 backdrop-blur-2xl border-b border-white/15 sticky top-0 z-50 shadow-2xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-4 group">
              <div className="flex items-center justify-center">
                <Image
                  src="/logo_bright.png"
                  alt="OxiWorld Forex Academy Logo"
                  width={64}
                  height={64}
                  className="object-contain transition-all duration-200 group-hover:scale-105"
                  priority
                />
              </div>
              <div className="hidden sm:block">
                <h1 className="text-2xl font-bold text-white group-hover:text-white/90 transition-colors duration-200">
                  OxiWorld
                </h1>
                <p className="text-xs text-gray-300">Forex Academy</p>
              </div>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-8">
              <Link 
                href="/" 
                className="text-white/80 hover:text-white font-medium transition-colors duration-200 px-3 py-2"
              >
                Home
              </Link>
              <Link 
                href="/courses" 
                className="text-white/80 hover:text-white font-medium transition-colors duration-200 px-3 py-2"
              >
                Education
              </Link>
              <Link 
                href="/market-analysis" 
                className="text-white/80 hover:text-white font-medium transition-colors duration-200 px-3 py-2"
              >
                Market Analysis
              </Link>
              <Link 
                href="/mentorship" 
                className="text-white/80 hover:text-white font-medium transition-colors duration-200 px-3 py-2"
              >
                Mentorship
              </Link>
              <Link 
                href="/signals" 
                className="text-white/80 hover:text-white font-medium transition-colors duration-200 px-3 py-2"
              >
                Signals
              </Link>
              <Link 
                href="/about" 
                className="text-white/80 hover:text-white font-medium transition-colors duration-200 px-3 py-2"
              >
                About
              </Link>
            </div>
          </div>

          {/* Auth Buttons */}
          <div className="hidden md:flex items-center space-x-4">
            {session?.user ? (
              <div className="flex items-center space-x-4">
                <Link 
                  href="/dashboard" 
                  className="text-white/90 hover:text-white font-medium transition-colors"
                >
                  Dashboard
                </Link>
                <Link 
                  href="/billing" 
                  className="text-white/90 hover:text-white font-medium transition-colors"
                >
                  Billing
                </Link>
                <div className="w-10 h-10 rounded-full bg-gradient-to-r from-[#00A17C] to-[#00A88F] flex items-center justify-center">
                  <span className="text-white text-sm font-medium">
                    {session.user.name?.charAt(0) || session.user.email?.charAt(0)}
                  </span>
                </div>
              </div>
            ) : (
              <div className="flex items-center space-x-6">
                <Link 
                  href="/auth" 
                  className="text-white/80 hover:text-white font-medium transition-colors duration-200 px-4 py-2"
                >
                  Sign In
                </Link>
                <Link 
                  href="/auth" 
                  className="bg-gradient-to-r from-[#00A17C] to-[#00A88F] text-white px-6 py-2.5 rounded-lg font-medium hover:from-[#009370] hover:to-[#009682] transition-all duration-200 shadow-lg hover:shadow-xl"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-white/80 hover:text-white p-2 transition-colors duration-200"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {isMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-[#000856]/95 backdrop-blur-xl border-t border-white/10">
              <Link 
                href="/" 
                className="block px-3 py-2 text-gray-300 hover:text-white font-medium rounded-md hover:bg-slate-700"
                onClick={() => setIsMenuOpen(false)}
              >
                Home
              </Link>
              <Link 
                href="/courses" 
                className="block px-3 py-2 text-gray-300 hover:text-white font-medium rounded-md hover:bg-slate-700"
                onClick={() => setIsMenuOpen(false)}
              >
                Education
              </Link>
              <Link 
                href="/market-analysis" 
                className="block px-3 py-2 text-gray-300 hover:text-white font-medium rounded-md hover:bg-slate-700"
                onClick={() => setIsMenuOpen(false)}
              >
                Market Analysis
              </Link>
              <Link 
                href="/mentorship" 
                className="block px-3 py-2 text-gray-300 hover:text-white font-medium rounded-md hover:bg-slate-700"
                onClick={() => setIsMenuOpen(false)}
              >
                Mentorship
              </Link>
              <Link 
                href="/signals" 
                className="block px-3 py-2 text-gray-300 hover:text-white font-medium rounded-md hover:bg-slate-700"
                onClick={() => setIsMenuOpen(false)}
              >
                Signals
              </Link>
              <Link 
                href="/about" 
                className="block px-3 py-2 text-gray-300 hover:text-white font-medium rounded-md hover:bg-slate-700"
                onClick={() => setIsMenuOpen(false)}
              >
                About
              </Link>
              
              {/* Mobile Auth */}
              <div className="pt-4 pb-3 border-t border-slate-700">
                {session?.user ? (
                  <div className="space-y-2">
                    <Link 
                      href="/dashboard" 
                      className="block px-3 py-2 bg-gradient-to-r from-[#00A17C] to-[#00A88F] text-white rounded-lg font-medium text-center"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      Dashboard
                    </Link>
                    <Link 
                      href="/billing" 
                      className="block px-3 py-2 text-gray-300 hover:text-white font-medium text-center rounded-md hover:bg-slate-700 border border-gray-600"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      Billing & Subscriptions
                    </Link>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Link 
                      href="/auth" 
                      className="block px-3 py-2 text-gray-300 hover:text-white font-medium text-center rounded-md hover:bg-slate-700"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      Sign In
                    </Link>
                    <Link 
                      href="/auth" 
                      className="block px-3 py-2 bg-gradient-to-r from-[#00A17C] to-[#00A88F] text-white rounded-lg font-medium text-center"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      Get Started
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}