'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useSession } from 'next-auth/react';
import Image from 'next/image';

export default function Navigation() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { data: session } = useSession();

  return (
    <nav className="bg-gradient-to-r from-[#000ABE] to-[#00B38F] backdrop-blur-md border-b border-[#00B39F]/30 sticky top-0 z-50 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-3">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center overflow-hidden">
                <Image
                  src="/logo_bright.png"
                  alt="OxiWorld Forex Academy Logo"
                  width={48}
                  height={48}
                  className="rounded-xl object-contain"
                  priority
                />
              </div>
              <div className="hidden sm:block">
                <h1 className="text-2xl font-bold text-white">
                  OxiWorld
                </h1>
                <p className="text-xs text-gray-400">Forex Academy</p>
              </div>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-8">
              <Link 
                href="/" 
                className="text-white/90 hover:text-white font-medium transition-colors px-3 py-2 rounded-md hover:bg-white/10 backdrop-blur-sm"
              >
                Home
              </Link>
              <Link 
                href="/courses" 
                className="text-white/90 hover:text-white font-medium transition-colors px-3 py-2 rounded-md hover:bg-white/10 backdrop-blur-sm"
              >
                Education
              </Link>
              <Link 
                href="/market-analysis" 
                className="text-white/90 hover:text-white font-medium transition-colors px-3 py-2 rounded-md hover:bg-white/10 backdrop-blur-sm"
              >
                Market Analysis
              </Link>
              <Link 
                href="/mentorship" 
                className="text-white/90 hover:text-white font-medium transition-colors px-3 py-2 rounded-md hover:bg-white/10 backdrop-blur-sm"
              >
                Mentorship
              </Link>
              <Link 
                href="/signals" 
                className="text-white/90 hover:text-white font-medium transition-colors px-3 py-2 rounded-md hover:bg-white/10 backdrop-blur-sm"
              >
                Signals
              </Link>
              <Link 
                href="/about" 
                className="text-white/90 hover:text-white font-medium transition-colors px-3 py-2 rounded-md hover:bg-white/10 backdrop-blur-sm"
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
                <div className="w-10 h-10 rounded-full bg-gradient-to-r from-[#00B38F] to-[#00B39F] flex items-center justify-center">
                  <span className="text-white text-sm font-medium">
                    {session.user.name?.charAt(0) || session.user.email?.charAt(0)}
                  </span>
                </div>
              </div>
            ) : (
              <div className="flex items-center space-x-4">
                <Link 
                  href="/auth" 
                  className="text-white/90 hover:text-white font-medium transition-colors px-4 py-2"
                >
                  Sign In
                </Link>
                <Link 
                  href="/auth" 
                  className="bg-gradient-to-r from-[#00B38F] to-[#00B39F] text-white px-6 py-2.5 rounded-lg font-medium hover:from-[#00A87D] hover:to-[#00A58D] transition-all duration-300 transform hover:scale-105 shadow-lg"
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
              className="text-white/90 hover:text-white p-2 hover:bg-white/10 rounded-md transition-colors"
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
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-slate-800 border-t border-slate-700">
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
                  <Link 
                    href="/dashboard" 
                    className="block px-3 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium text-center"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Dashboard
                  </Link>
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
                      className="block px-3 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium text-center"
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