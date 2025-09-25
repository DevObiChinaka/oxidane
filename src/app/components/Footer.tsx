'use client';

import Link from 'next/link';
import Image from 'next/image';

export default function Footer() {
  return (
    <footer className="bg-gradient-to-r from-[#000ABE] to-[#032DA0] text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 rounded-lg flex items-center justify-center overflow-hidden">
                <Image
                  src="/blue_icon.png"
                  alt="OxY Fx Logo"
                  width={48}
                  height={48}
                  className="rounded-lg object-contain"
                  priority
                />
              </div>
              <div>
                <h3 className="text-xl font-bold">OxiWorld</h3>
                <p className="text-sm text-gray-400">Forex Academy</p>
              </div>
            </div>
            <p className="text-gray-400 text-sm leading-relaxed">
              Transform your trading with world-class education, expert mentorship, 
              and professional signals from industry leaders.
            </p>
            <div className="flex space-x-4">
              <a href="#" className="text-gray-400 hover:text-[#00B39F] transition-colors">
                <span className="sr-only">Telegram</span>
                <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M9.78 18.65l.28-4.23 7.68-6.92c.34-.31-.07-.46-.52-.19L7.74 13.3 3.64 12c-.88-.25-.89-.86.2-1.3l15.97-6.16c.73-.33 1.43.18 1.15 1.3l-2.72 12.81c-.19.91-.74 1.13-1.5.71L12.6 16.3l-1.99 1.93c-.23.23-.42.42-.83.42z"/>
                </svg>
              </a>
              <a href="#" className="text-gray-400 hover:text-[#00B39F] transition-colors">
                <span className="sr-only">YouTube</span>
                <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                </svg>
              </a>
              <a href="#" className="text-gray-400 hover:text-[#00B39F] transition-colors">
                <span className="sr-only">Instagram</span>
                <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 6.62 5.367 11.987 11.988 11.987c6.62 0 11.987-5.367 11.987-11.987C24.014 5.367 18.637.001 12.017.001zM8.449 16.988c-1.297 0-2.448-.49-3.33-1.297L3.722 14.3c-.886-.807-1.297-1.953-1.297-3.33s.49-2.448 1.297-3.33L5.119 6.243c.807-.886 1.953-1.297 3.33-1.297s2.448.49 3.33 1.297L13.176 7.64c.886.807 1.297 1.953 1.297 3.33s-.49 2.448-1.297 3.33L11.779 15.69c-.807.886-1.953 1.297-3.33 1.297z"/>
                </svg>
              </a>
            </div>
          </div>

          {/* Education */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold">Education</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/courses" className="text-gray-400 hover:text-white transition-colors">Free Courses</Link></li>
              <li><Link href="/beginner" className="text-gray-400 hover:text-white transition-colors">Beginner Guide</Link></li>
              <li><Link href="/advanced" className="text-gray-400 hover:text-white transition-colors">Advanced Strategies</Link></li>
              <li><Link href="/resources" className="text-gray-400 hover:text-white transition-colors">Trading Resources</Link></li>
              <li><Link href="/blog" className="text-gray-400 hover:text-white transition-colors">Market Analysis</Link></li>
            </ul>
          </div>

          {/* Services */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold">Services</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/mentorship" className="text-gray-400 hover:text-white transition-colors">1-on-1 Mentorship</Link></li>
              <li><Link href="/signals" className="text-gray-400 hover:text-white transition-colors">Trading Signals</Link></li>
              <li><Link href="/consulting" className="text-gray-400 hover:text-white transition-colors">Portfolio Review</Link></li>
              <li><Link href="/community" className="text-gray-400 hover:text-white transition-colors">Trading Community</Link></li>
              <li><Link href="/support" className="text-gray-400 hover:text-white transition-colors">24/7 Support</Link></li>
            </ul>
          </div>

          {/* Company */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold">Company</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/about" className="text-gray-400 hover:text-white transition-colors">About Us</Link></li>
              <li><Link href="/contact" className="text-gray-400 hover:text-white transition-colors">Contact</Link></li>
              <li><Link href="/careers" className="text-gray-400 hover:text-white transition-colors">Careers</Link></li>
              <li><Link href="/privacy" className="text-gray-400 hover:text-white transition-colors">Privacy Policy</Link></li>
              <li><Link href="/terms" className="text-gray-400 hover:text-white transition-colors">Terms of Service</Link></li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-[#00B39F]/30 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center">
          <p className="text-gray-400 text-sm">
            © 2025 Oxidane Forex Academy. All rights reserved.
          </p>
          <div className="flex items-center space-x-6 mt-4 md:mt-0">
            <span className="text-gray-400 text-sm">Risk Warning: Trading involves risk</span>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-green-500 text-sm font-medium">Markets Open</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}