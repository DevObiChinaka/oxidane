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
        
        {/* Customer Support Icon - Person with Headset */}
        <svg
          className="w-6 h-6 text-white relative z-10"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          {/* Headset */}
          <path d="M12 1C7.03 1 3 5.03 3 10v5c0 1.1.9 2 2 2h1v-7H5v-1c0-3.87 3.13-7 7-7s7 3.13 7 7v1h-1v7h1c1.1 0 2-.9 2-2v-5c0-4.97-4.03-9-9-9z"/>
          {/* Left ear cup */}
          <path d="M5 12h2v7H5z"/>
          {/* Right ear cup */}
          <path d="M17 12h2v7h-2z"/>
          {/* Microphone */}
          <path d="M12 19c-1.1 0-2 .9-2 2v1h4v-1c0-1.1-.9-2-2-2z"/>
          {/* Person head (circle) */}
          <circle cx="12" cy="10" r="3"/>
        </svg>
      </div>
    </a>
  );
}
