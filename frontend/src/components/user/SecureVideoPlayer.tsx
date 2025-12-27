'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
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

// Hook to detect mobile devices
function useIsMobile() {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768 || 
        /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      setIsMobile(mobile);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  return isMobile;
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
  const [isImmersive, setIsImmersive] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const isMobile = useIsMobile();

  // Toggle immersive mode (mobile fullscreen alternative)
  const toggleImmersive = useCallback(() => {
    if (!isMobile) return;
    
    setIsImmersive(prev => {
      const newValue = !prev;
      
      // Lock/unlock body scroll
      if (newValue) {
        document.body.style.overflow = 'hidden';
        // Force landscape orientation hint on supported browsers
        if (screen.orientation && (screen.orientation as any).lock) {
          (screen.orientation as any).lock('landscape').catch(() => {
            // Orientation lock not supported or denied
          });
        }
      } else {
        document.body.style.overflow = '';
        if (screen.orientation && (screen.orientation as any).unlock) {
          (screen.orientation as any).unlock();
        }
      }
      
      return newValue;
    });
  }, [isMobile]);

  // Notify iframe when immersive mode changes (for fullscreen icon state)
  useEffect(() => {
    if (iframeRef.current && iframeRef.current.contentWindow) {
      iframeRef.current.contentWindow.postMessage({
        type: 'fullscreenChange',
        isFullscreen: isImmersive
      }, '*');
    }
  }, [isImmersive]);

  // Handle back button to exit immersive mode
  useEffect(() => {
    if (!isImmersive) return;
    
    const handlePopState = (e: PopStateEvent) => {
      e.preventDefault();
      setIsImmersive(false);
      document.body.style.overflow = '';
      // Push state back so user can navigate normally after
      window.history.pushState(null, '', window.location.href);
    };
    
    // Push a state so back button triggers our handler
    window.history.pushState(null, '', window.location.href);
    window.addEventListener('popstate', handlePopState);
    
    return () => {
      window.removeEventListener('popstate', handlePopState);
      document.body.style.overflow = '';
    };
  }, [isImmersive]);

  useEffect(() => {
    // Reset state when lessonId changes
    setLoading(true);
    setError(null);
    
    // If we have a preloaded embed, use it immediately
    if (preloadedEmbed) {
      setEmbedHtml(preloadedEmbed);
      
      // Give YouTube IFrame API time to initialize (it loads async inside srcDoc)
      setTimeout(() => {
        setLoading(false);
      }, 1500);
    } else if (!isPreloading) {
      // Fallback: fetch if not preloaded and not currently preloading
      loadVideoEmbed();
    } else {
      // Still preloading, show loading state
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
    
    // Handle fullscreen requests from embedded video via PostMessage
    const handleMessage = (event: MessageEvent) => {
      if (event.data && event.data.type === 'toggleFullscreen') {
        const iframe = iframeRef.current;
        if (!iframe) return;
        
        // On mobile, use immersive mode instead of native fullscreen
        if (isMobile) {
          toggleImmersive();
          return;
        }
        
        // Check current fullscreen state
        const isFullscreen = document.fullscreenElement || 
                            (document as any).webkitFullscreenElement || 
                            (document as any).mozFullScreenElement || 
                            (document as any).msFullscreenElement;
        
        if (isFullscreen) {
          // Exit fullscreen
          if (document.exitFullscreen) {
            document.exitFullscreen();
          } else if ((document as any).webkitExitFullscreen) {
            (document as any).webkitExitFullscreen();
          } else if ((document as any).mozCancelFullScreen) {
            (document as any).mozCancelFullScreen();
          } else if ((document as any).msExitFullscreen) {
            (document as any).msExitFullscreen();
          }
        } else {
          // Enter fullscreen on the iframe element
          try {
            if (iframe.requestFullscreen) {
              iframe.requestFullscreen();
            } else if ((iframe as any).webkitRequestFullscreen) {
              (iframe as any).webkitRequestFullscreen();
            } else if ((iframe as any).webkitEnterFullscreen) {
              (iframe as any).webkitEnterFullscreen();
            } else if ((iframe as any).mozRequestFullScreen) {
              (iframe as any).mozRequestFullScreen();
            } else if ((iframe as any).msRequestFullscreen) {
              (iframe as any).msRequestFullscreen();
            }
          } catch (err) {
            console.error('Fullscreen error:', err);
          }
        }
      }
    };
    
    // Handle fullscreen change to notify the embedded video
    const handleFullscreenChange = () => {
      const isFullscreen = !!(document.fullscreenElement || 
                            (document as any).webkitFullscreenElement || 
                            (document as any).mozFullScreenElement || 
                            (document as any).msFullscreenElement);
      
      // Notify the iframe about fullscreen state change
      if (iframeRef.current && iframeRef.current.contentWindow) {
        iframeRef.current.contentWindow.postMessage({
          type: 'fullscreenChange',
          isFullscreen: isFullscreen || isImmersive
        }, '*');
      }
    };

    document.addEventListener('contextmenu', handleContextMenu);
    document.addEventListener('keydown', handleKeyDown);
    window.addEventListener('message', handleMessage);
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', handleFullscreenChange);
    document.addEventListener('MSFullscreenChange', handleFullscreenChange);

    return () => {
      document.removeEventListener('contextmenu', handleContextMenu);
      document.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('message', handleMessage);
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
      document.removeEventListener('mozfullscreenchange', handleFullscreenChange);
      document.removeEventListener('MSFullscreenChange', handleFullscreenChange);
    };
  }, [isMobile, toggleImmersive, isImmersive]);

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

      setEmbedHtml(data.embed_html);
      setLoading(false);

    } catch (err: any) {
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
    <div 
      ref={containerRef}
      className={`relative ${className} ${isImmersive ? '' : ''}`} 
      style={{ 
        userSelect: 'none', 
        position: isImmersive ? 'fixed' : 'relative', 
        width: isImmersive ? '100vw' : '100%', 
        height: isImmersive ? '100vh' : '100%',
        ...(isImmersive ? { top: 0, left: 0, zIndex: 9999, backgroundColor: '#000' } : {})
      }}
    >
      {/* Exit immersive mode button (mobile only) */}
      {isImmersive && (
        <button
          onClick={toggleImmersive}
          className="absolute top-4 right-4 z-50 bg-black/60 hover:bg-black/80 text-white p-2 rounded-full transition-colors"
          aria-label="Exit fullscreen"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}

      {/* Rotate phone hint in immersive mode (portrait orientation) */}
      {isImmersive && isMobile && (
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-50 portrait:block landscape:hidden">
          <div className="bg-black/70 text-white/80 px-3 py-1.5 rounded-full text-xs flex items-center space-x-2">
            <svg className="w-4 h-4 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>Rotate for better view</span>
          </div>
        </div>
      )}

      {/* Main Video Container */}
      <div className="relative w-full h-full bg-black" style={{ position: 'relative' }}>
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900 z-20">
            <div className="text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-4 border-gray-700 border-t-[#00B38F] mx-auto mb-4"></div>
              <p className="text-gray-400 text-lg">Loading video...</p>
            </div>
          </div>
        )}
        {embedHtml && (
          <iframe
            key={`video-${lessonId}`}
            ref={iframeRef}
            srcDoc={embedHtml}
            className="w-full h-full border-0"
            allowFullScreen
            allow="autoplay; encrypted-media; picture-in-picture; fullscreen"
            title={lessonTitle}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%'
            }}
            // Add comprehensive fullscreen support for all browsers including Safari
            {...({
              'webkitallowfullscreen': 'true',
              'mozallowfullscreen': 'true',
              'allowfullscreen': 'true',
              'webkit-playsinline': 'true',
              'playsinline': 'true'
            } as any)}
          />
        )}
        
        {/* Invisible overlay to prevent direct iframe manipulation */}
        {embedHtml && (
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