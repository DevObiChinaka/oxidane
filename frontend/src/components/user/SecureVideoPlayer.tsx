'use client';

import { useState, useEffect, useRef } from 'react';
import { API_ENDPOINTS } from '@/config/api';

interface SecureVideoPlayerProps {
  lessonId: string;
  lessonTitle: string;
  videoSource: 'youtube' | 'vimeo' | 'upload';
  onVideoEnd?: () => void;
  className?: string;
  preloadedEmbed?: string;  // Pre-loaded embed HTML from cache
  isPreloading?: boolean;   // Whether embeds are still being pre-loaded
}

export default function SecureVideoPlayer({
  lessonId,
  lessonTitle,
  onVideoEnd,
  className = '',
  preloadedEmbed,
  isPreloading = false
}: SecureVideoPlayerProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [embedHtml, setEmbedHtml] = useState<string>('');
  const [blobUrl, setBlobUrl] = useState<string>('');
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    console.log('[VIDEO_PLAYER] Loading video for lesson:', lessonId);
    
    // Cleanup previous blob URL
    return () => {
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [lessonId]);

  useEffect(() => {
    // If we have a preloaded embed, use it immediately
    if (preloadedEmbed) {
      console.log('[VIDEO_PLAYER] Using pre-loaded embed');
      setEmbedHtml(preloadedEmbed);
      
      // Convert HTML to Blob URL for proper iframe loading
      const blob = new Blob([preloadedEmbed], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      setBlobUrl(url);
      
      setLoading(false);
      setError(null);
    } else if (!isPreloading) {
      // Fallback: fetch if not preloaded and not currently preloading
      console.log('[VIDEO_PLAYER] Fetching embed (not cached)');
      setLoading(true);
      setError(null);
      loadVideoEmbed();
    }
  }, [lessonId, preloadedEmbed, isPreloading]);

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

      // Add timestamp to prevent any caching
      const timestamp = new Date().getTime();
      const apiUrl = `${API_ENDPOINTS.user.videoEmbed(lessonId)}?t=${timestamp}`;
      
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        cache: 'no-store'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || errorData.error || 'Failed to load video');
      }

      const data = await response.json();
      console.log('[VIDEO_PLAYER] Video loaded successfully');

      setEmbedHtml(data.embed_html);
      
      // Convert HTML to Blob URL
      const blob = new Blob([data.embed_html], { type: 'text/html' });
      const blobObjectUrl = URL.createObjectURL(blob);
      setBlobUrl(blobObjectUrl);
      
      setLoading(false);

    } catch (err: any) {
      console.error('[VIDEO_PLAYER] Error:', err);
      setError(err.message || 'Failed to load video');
      setLoading(false);
    }
  };

  if (loading || isPreloading) {
    return (
      <div className={`flex items-center justify-center bg-gray-900 ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-gray-700 border-t-[#00B38F] mx-auto mb-4"></div>
          <p className="text-gray-400 text-lg">
            {isPreloading ? 'Preparing videos...' : 'Loading video...'}
          </p>
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
        {blobUrl && (
          <iframe
            key={`video-${lessonId}`}
            ref={iframeRef}
            src={blobUrl}
            className="w-full h-full border-0"
            allowFullScreen
            allow="autoplay; encrypted-media; picture-in-picture; fullscreen"
            title={lessonTitle}
            // Add mobile fullscreen support
            {...({
              'webkitallowfullscreen': 'true',
              'mozallowfullscreen': 'true',
              'allowfullscreen': 'true'
            } as any)}
          />
        )}
        
        {/* Invisible overlay to prevent direct iframe manipulation */}
        {blobUrl && (
          <div 
            className="absolute inset-0 pointer-events-none"
            style={{ zIndex: 1 }}
            onContextMenu={(e) => e.preventDefault()}
          />
        )}
      </div>
    </div>
  );
}
