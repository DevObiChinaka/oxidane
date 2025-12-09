'use client';

import { useState, useEffect, useRef } from 'react';
import { API_ENDPOINTS } from '@/config/api';

interface SecureVideoPlayerProps {
  lessonId: string;
  lessonTitle: string;
  videoSource: 'youtube' | 'vimeo' | 'upload';
  onVideoEnd?: () => void;
  className?: string;
}

export default function SecureVideoPlayer({
  lessonId,
  lessonTitle,
  onVideoEnd,
  className = ''
}: SecureVideoPlayerProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [embedHtml, setEmbedHtml] = useState<string>('');
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    loadVideoEmbed();
  }, [lessonId]);

  useEffect(() => {
    // Disable right-click and keyboard shortcuts on mount
    const handleContextMenu = (e: MouseEvent) => {
      e.preventDefault();
      return false;
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      // F12, Ctrl+Shift+I, Ctrl+Shift+J, Ctrl+U
      if (
        e.keyCode === 123 || // F12
        (e.ctrlKey && e.shiftKey && e.keyCode === 73) || // Ctrl+Shift+I
        (e.ctrlKey && e.shiftKey && e.keyCode === 74) || // Ctrl+Shift+J
        (e.ctrlKey && e.keyCode === 85) // Ctrl+U
      ) {
        e.preventDefault();
        return false;
      }
    };

    document.addEventListener('contextmenu', handleContextMenu);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('contextmenu', handleContextMenu);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const loadVideoEmbed = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('user_auth_token') || localStorage.getItem('access_token');
      if (!token) {
        setError('Please log in to watch this video');
        setLoading(false);
        return;
      }

      const response = await fetch(
        API_ENDPOINTS.user.videoEmbed(lessonId),
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || errorData.error || 'Failed to load video');
      }

      const data = await response.json();
      console.log('[VIDEO_PLAYER] Video loaded successfully');

      setEmbedHtml(data.embed_html);
      setLoading(false);

    } catch (err: any) {
      console.error('[VIDEO_PLAYER] Error:', err);
      setError(err.message || 'Failed to load video');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center bg-gray-900 ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-gray-700 border-t-[#00B38F] mx-auto mb-4"></div>
          <p className="text-gray-400 text-lg">Loading video...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center bg-gray-900 ${className}`}>
        <div className="text-center px-6">
          <div className="w-20 h-20 mx-auto mb-6 bg-red-900/20 rounded-full flex items-center justify-center">
            <svg className="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">Unable to Load Video</h3>
          <p className="text-gray-400 mb-6">{error}</p>
          <button
            onClick={loadVideoEmbed}
            className="px-6 py-3 bg-[#00B38F] hover:bg-[#009975] text-white rounded-lg transition-colors font-medium"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`} style={{ userSelect: 'none' }}>
      {/* Main Video Container */}
      <div className="relative w-full h-full bg-black">
        <iframe
          ref={iframeRef}
          srcDoc={embedHtml}
          className="w-full h-full border-0"
          allowFullScreen
          allow="autoplay; encrypted-media; picture-in-picture; fullscreen"
          sandbox="allow-same-origin allow-scripts allow-presentation allow-forms"
          title={lessonTitle}
        />
        
        {/* Invisible overlay to prevent direct iframe manipulation */}
        <div 
          className="absolute inset-0 pointer-events-none"
          style={{ zIndex: 1 }}
          onContextMenu={(e) => e.preventDefault()}
        />
      </div>
    </div>
  );
}
