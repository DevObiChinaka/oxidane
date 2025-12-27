'use client';

import { useState } from 'react';

export default function WhatsAppSupport() {
  const [isHovered, setIsHovered] = useState(false);
  
  // WhatsApp number (remove + and spaces for the link)
  const whatsappNumber = '2349054565499';
  const whatsappMessage = encodeURIComponent('Hello! I need help with OxiWorld Forex Academy.');
  const whatsappLink = `https://wa.me/${whatsappNumber}?text=${whatsappMessage}`;

  return (
    <a
      href={whatsappLink}
      target="_blank"
      rel="noopener noreferrer"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="fixed bottom-6 right-6 z-50 flex items-center group"
      aria-label="Chat with us on WhatsApp"
    >
      {/* Tooltip/Label - slides in on hover */}
      <div
        className={`
          mr-3 px-4 py-2 bg-white rounded-lg shadow-lg
          transition-all duration-300 ease-out
          ${isHovered ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-4 pointer-events-none'}
        `}
      >
        <p className="text-sm font-medium text-gray-800 whitespace-nowrap">Need help? Chat with us</p>
      </div>

      {/* Support Button */}
      <div
        className={`
          relative flex items-center justify-center
          w-12 h-12 rounded-full
          bg-[#00B39F] hover:bg-[#009985]
          shadow-lg hover:shadow-xl
          transition-all duration-300 ease-out
          ${isHovered ? 'scale-110' : 'scale-100'}
        `}
      >
        {/* Pulse animation ring */}
        <div className="absolute inset-0 rounded-full bg-[#00B39F] animate-ping opacity-25"></div>
        
        {/* Customer Support Icon - Person with Headset & Mic */}
        <svg
          className="w-6 h-6 text-white relative z-10"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          {/* Head/Face outline */}
          <path d="M12 2C9.24 2 7 4.24 7 7v3c0 2.76 2.24 5 5 5s5-2.24 5-5V7c0-2.76-2.24-5-5-5z" fillOpacity="0"/>
          <path d="M12 2C9.24 2 7 4.24 7 7v4c0 2.76 2.24 5 5 5s5-2.24 5-5V7c0-2.76-2.24-5-5-5zm0 12c-1.66 0-3-1.34-3-3V7c0-1.66 1.34-3 3-3s3 1.34 3 3v4c0 1.66-1.34 3-3 3z"/>
          {/* Hair */}
          <path d="M7 7c0-2.76 2.24-5 5-5s5 2.24 5 5v1c0-2.21-1.79-4-4-4h-2c-2.21 0-4 1.79-4 4V7z"/>
          {/* Headset band */}
          <path d="M4 11c0-4.42 3.58-8 8-8s8 3.58 8 8" fill="none" stroke="currentColor" strokeWidth="2"/>
          {/* Left earpiece */}
          <rect x="2" y="10" width="3" height="5" rx="1"/>
          {/* Right earpiece */}
          <rect x="19" y="10" width="3" height="5" rx="1"/>
          {/* Microphone arm */}
          <path d="M19 15c0 1.1-.9 2-2 2h-3" fill="none" stroke="currentColor" strokeWidth="1.5"/>
          {/* Microphone */}
          <circle cx="13" cy="17" r="2"/>
        </svg>
      </div>
    </a>
  );
}
