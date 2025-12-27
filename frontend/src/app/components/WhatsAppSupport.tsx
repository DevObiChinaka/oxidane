'use client';

import { useState } from 'react';
import { ChatBubbleLeftRightIcon } from '@heroicons/react/24/solid';

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
        
        {/* Support Icon from Heroicons */}
        <ChatBubbleLeftRightIcon className="w-6 h-6 text-white relative z-10" />
      </div>
    </a>
  );
}
