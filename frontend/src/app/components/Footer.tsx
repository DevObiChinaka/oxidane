'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useRouter, usePathname } from 'next/navigation';

export default function Footer() {
  const router = useRouter();
  const pathname = usePathname();

  // Smart navigation handler for hash links
  const handleHashNavigation = (hash: string) => {
    if (pathname === '/') {
      // On landing page - smooth scroll to section
      const element = document.getElementById(hash.replace('#', ''));
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    } else {
      // On other pages - navigate to landing page with hash
      router.push(`/${hash}`);
    }
  };
  return (
    <footer className="bg-[#000856]/95 backdrop-blur-2xl border-t border-white/15 text-white">
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
              <a href="https://t.me/tradewithoxidane" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-[#00B39F] transition-colors">
                <span className="sr-only">Telegram</span>
                <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M9.78 18.65l.28-4.23 7.68-6.92c.34-.31-.07-.46-.52-.19L7.74 13.3 3.64 12c-.88-.25-.89-.86.2-1.3l15.97-6.16c.73-.33 1.43.18 1.15 1.3l-2.72 12.81c-.19.91-.74 1.13-1.5.71L12.6 16.3l-1.99 1.93c-.23.23-.42.42-.83.42z"/>
                </svg>
              </a>
              <a href="https://www.youtube.com/channel/UCWIKCG9AppJAJrSyMTGhOFQ" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-[#00B39F] transition-colors">
                <span className="sr-only">YouTube</span>
                <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                </svg>
              </a>
              <a href="https://www.tiktok.com/@morrisoxidane" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-[#00B39F] transition-colors">
                <span className="sr-only">TikTok</span>
                <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-.88-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z"/>
                </svg>
              </a>
              <a href="https://x.com/MorrisOxidane" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-[#00B39F] transition-colors">
                <span className="sr-only">X (Twitter)</span>
                <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                </svg>
              </a>
            </div>
          </div>

          {/* Education */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold">Education</h4>
            <ul className="space-y-2 text-sm">
              <li><button onClick={() => handleHashNavigation('#services')} className="text-gray-400 hover:text-white transition-colors cursor-pointer">Trading Education</button></li>
              <li><button onClick={() => handleHashNavigation('#hero')} className="text-gray-400 hover:text-white transition-colors cursor-pointer">Market Analysis</button></li>
              <li><button onClick={() => handleHashNavigation('#educational-value')} className="text-gray-400 hover:text-white transition-colors cursor-pointer">Free Resources</button></li>
              <li><Link href="/auth" className="text-gray-400 hover:text-white transition-colors">Access Learning</Link></li>
              <li><button onClick={() => handleHashNavigation('#testimonials')} className="text-gray-400 hover:text-white transition-colors cursor-pointer">Success Stories</button></li>
            </ul>
          </div>

          {/* Services */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold">Services</h4>
            <ul className="space-y-2 text-sm">
              <li><button onClick={() => handleHashNavigation('#services')} className="text-gray-400 hover:text-white transition-colors cursor-pointer">Forex Signals</button></li>
              <li><button onClick={() => handleHashNavigation('#services')} className="text-gray-400 hover:text-white transition-colors cursor-pointer">Community Mentorship</button></li>
              <li><Link href="/pricing" className="text-gray-400 hover:text-white transition-colors">Pricing Plans</Link></li>
              <li><Link href="/auth" className="text-gray-400 hover:text-white transition-colors">Join Community</Link></li>
              <li><button onClick={() => handleHashNavigation('#hero')} className="text-gray-400 hover:text-white transition-colors cursor-pointer">Live Market Data</button></li>
            </ul>
          </div>

          {/* Company */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold">Company</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="#testimonials" className="text-gray-400 hover:text-white transition-colors cursor-pointer">Our Results</a></li>
              <li><Link href="/auth" className="text-gray-400 hover:text-white transition-colors">Get Started</Link></li>
              <li><Link href="/privacy" className="text-gray-400 hover:text-white transition-colors">Privacy Policy</Link></li>
              <li><a href="#hero" className="text-gray-400 hover:text-white transition-colors cursor-pointer">Professional Trading</a></li>
              <li><a href="#services" className="text-gray-400 hover:text-white transition-colors cursor-pointer">Why Choose Us</a></li>
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