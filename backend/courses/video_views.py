"""
Video streaming endpoints with enrollment-based access control
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Lesson
from .video_security import (
    extract_youtube_video_id,
    extract_vimeo_video_id,
    check_user_lesson_access
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_video_embed(request, lesson_id):
    """
    Get video embed HTML for authenticated and enrolled users
    
    GET /api/lessons/{lesson_id}/video-embed/
    
    Returns:
        {
            "embed_html": "<html>...</html>",
            "lesson_id": "...",
            "lesson_title": "..."
        }
    """
    try:
        lesson = get_object_or_404(Lesson, id=lesson_id)
        user = request.user
        
        # Check if user has access to this lesson
        if not check_user_lesson_access(user, lesson):
            return Response({
                'error': 'Access denied',
                'message': 'You must be enrolled in this course to access this lesson'
            }, status=status.HTTP_403_FORBIDDEN)
        
        print(f"[VIDEO_EMBED] Serving video for {user.email} - {lesson.title}")
        print(f"[VIDEO_EMBED] Source: {lesson.video_source}")
        
        # Generate embed HTML based on video source
        embed_html = generate_embed_html(lesson)
        
        return Response({
            'embed_html': embed_html,
            'lesson_id': str(lesson.id),
            'lesson_title': lesson.title
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'error': 'Failed to generate video embed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def generate_embed_html(lesson):
    """
    Generate secure embed HTML for different video sources
    
    Args:
        lesson: Lesson instance
        access_token: Access token for security
    
    Returns:
        str: HTML string with embedded video player
    """
    if lesson.video_source == 'youtube':
        video_id = lesson.youtube_video_id or extract_youtube_video_id(lesson.video_url)
        
        if not video_id:
            return generate_error_html("YouTube video ID not found")
        
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ 
            height: 100%; 
            overflow: hidden; 
            background: #000; 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}
        #video-container {{
            position: relative;
            width: 100%;
            height: 100%;
        }}
        #player {{
            width: 100%;
            height: 100%;
            pointer-events: none;
        }}
        #controls-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 10;
            cursor: pointer;
        }}
        #controls {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
            padding: 20px 15px 15px;
            opacity: 0;
            transition: opacity 0.3s;
        }}
        #controls-overlay:hover #controls,
        #controls.show {{
            opacity: 1;
        }}
        #progress-container {{
            width: 100%;
            height: 5px;
            background: rgba(255,255,255,0.3);
            border-radius: 3px;
            cursor: pointer;
            margin-bottom: 10px;
        }}
        #progress-bar {{
            height: 100%;
            background: #00B38F;
            border-radius: 3px;
            width: 0%;
            transition: width 0.1s;
        }}
        #controls-buttons {{
            display: flex;
            align-items: center;
            gap: 15px;
            color: white;
        }}
        .control-btn {{
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            padding: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s;
        }}
        .control-btn:hover {{
            transform: scale(1.1);
        }}
        .control-btn:active {{
            transform: scale(0.95);
        }}
        #time-display {{
            font-size: 14px;
            color: white;
            margin-left: auto;
        }}
        #volume-container {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        #volume-slider {{
            width: 70px;
            height: 4px;
            -webkit-appearance: none;
            background: rgba(255,255,255,0.3);
            border-radius: 2px;
            outline: none;
        }}
        #volume-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 12px;
            height: 12px;
            background: #00B38F;
            border-radius: 50%;
            cursor: pointer;
        }}
        #center-play {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 80px;
            height: 80px;
            background: rgba(0, 179, 143, 0.9);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.3s;
            pointer-events: none;
        }}
        #center-play.show {{
            opacity: 1;
        }}
    </style>
</head>
<body>
    <div id="video-container">
        <div id="player"></div>
        <div id="controls-overlay">
            <div id="center-play">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="white">
                    <path d="M8 5v14l11-7z"/>
                </svg>
            </div>
            <div id="controls">
                <div id="progress-container">
                    <div id="progress-bar"></div>
                </div>
                <div id="controls-buttons">
                    <button class="control-btn" id="play-pause">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="white" id="play-icon">
                            <path d="M8 5v14l11-7z"/>
                        </svg>
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="white" id="pause-icon" style="display:none;">
                            <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
                        </svg>
                    </button>
                    <button class="control-btn" id="rewind">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                            <path d="M11 18V6l-8.5 6 8.5 6zm.5-6l8.5 6V6l-8.5 6z"/>
                        </svg>
                        <span style="font-size:10px; margin-left:-18px;">10</span>
                    </button>
                    <button class="control-btn" id="forward">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                            <path d="M4 18l8.5-6L4 6v12zm9-12v12l8.5-6L13 6z"/>
                        </svg>
                        <span style="font-size:10px; margin-left:-18px;">10</span>
                    </button>
                    <div id="volume-container">
                        <button class="control-btn" id="mute">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="white" id="volume-icon">
                                <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/>
                            </svg>
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="white" id="mute-icon" style="display:none;">
                                <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
                            </svg>
                        </button>
                        <input type="range" id="volume-slider" min="0" max="100" value="100">
                    </div>
                    <span id="time-display">0:00 / 0:00</span>
                    <button class="control-btn" id="fullscreen">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                            <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://www.youtube.com/iframe_api"></script>
    <script>
        let player;
        let isPlaying = false;
        let controlsTimeout;

        // Disable right-click
        document.addEventListener('contextmenu', e => {{
            e.preventDefault();
            return false;
        }}, true);

        // Disable DevTools shortcuts
        document.addEventListener('keydown', e => {{
            if (e.keyCode === 123 || 
                (e.ctrlKey && e.shiftKey && (e.keyCode === 73 || e.keyCode === 74)) ||
                (e.ctrlKey && e.keyCode === 85) ||
                (e.ctrlKey && e.keyCode === 83)) {{
                e.preventDefault();
                return false;
            }}
            
            // Space bar for play/pause
            if (e.keyCode === 32 && e.target.tagName !== 'INPUT') {{
                e.preventDefault();
                togglePlay();
            }}
            // Arrow keys for seek
            if (e.keyCode === 37) {{ // Left arrow
                e.preventDefault();
                rewind();
            }}
            if (e.keyCode === 39) {{ // Right arrow
                e.preventDefault();
                forward();
            }}
        }}, true);

        // Disable text selection
        document.body.style.userSelect = 'none';
        document.body.style.webkitUserSelect = 'none';

        function onYouTubeIframeAPIReady() {{
            player = new YT.Player('player', {{
                height: '100%',
                width: '100%',
                videoId: '{video_id}',
                playerVars: {{
                    'autoplay': 1,
                    'controls': 0,
                    'rel': 0,
                    'modestbranding': 1,
                    'fs': 0,
                    'iv_load_policy': 3,
                    'disablekb': 1
                }},
                events: {{
                    'onReady': onPlayerReady,
                    'onStateChange': onPlayerStateChange
                }}
            }});
        }}

        function onPlayerReady(event) {{
            updateProgressBar();
            setInterval(updateProgressBar, 100);
        }}

        function onPlayerStateChange(event) {{
            if (event.data === YT.PlayerState.PLAYING) {{
                isPlaying = true;
                document.getElementById('play-icon').style.display = 'none';
                document.getElementById('pause-icon').style.display = 'block';
                document.getElementById('center-play').classList.remove('show');
            }} else {{
                isPlaying = false;
                document.getElementById('play-icon').style.display = 'block';
                document.getElementById('pause-icon').style.display = 'none';
            }}
        }}

        function togglePlay() {{
            if (!player) return;
            if (isPlaying) {{
                player.pauseVideo();
                document.getElementById('center-play').classList.add('show');
            }} else {{
                player.playVideo();
            }}
        }}

        function rewind() {{
            if (!player) return;
            const currentTime = player.getCurrentTime();
            player.seekTo(Math.max(0, currentTime - 10), true);
        }}

        function forward() {{
            if (!player) return;
            const currentTime = player.getCurrentTime();
            const duration = player.getDuration();
            player.seekTo(Math.min(duration, currentTime + 10), true);
        }}

        function updateProgressBar() {{
            if (!player || !player.getDuration) return;
            const currentTime = player.getCurrentTime();
            const duration = player.getDuration();
            const progress = (currentTime / duration) * 100;
            document.getElementById('progress-bar').style.width = progress + '%';
            
            document.getElementById('time-display').textContent = 
                formatTime(currentTime) + ' / ' + formatTime(duration);
        }}

        function formatTime(seconds) {{
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return mins + ':' + (secs < 10 ? '0' : '') + secs;
        }}

        // Event Listeners
        document.getElementById('play-pause').addEventListener('click', togglePlay);
        document.getElementById('rewind').addEventListener('click', rewind);
        document.getElementById('forward').addEventListener('click', forward);
        
        document.getElementById('controls-overlay').addEventListener('click', (e) => {{
            if (e.target.id === 'controls-overlay' || e.target.id === 'center-play') {{
                togglePlay();
            }}
        }});

        document.getElementById('progress-container').addEventListener('click', (e) => {{
            if (!player) return;
            const rect = e.currentTarget.getBoundingClientRect();
            const pos = (e.clientX - rect.left) / rect.width;
            player.seekTo(pos * player.getDuration(), true);
        }});

        document.getElementById('mute').addEventListener('click', () => {{
            if (!player) return;
            if (player.isMuted()) {{
                player.unMute();
                document.getElementById('volume-icon').style.display = 'block';
                document.getElementById('mute-icon').style.display = 'none';
                document.getElementById('volume-slider').value = player.getVolume();
            }} else {{
                player.mute();
                document.getElementById('volume-icon').style.display = 'none';
                document.getElementById('mute-icon').style.display = 'block';
            }}
        }});

        document.getElementById('volume-slider').addEventListener('input', (e) => {{
            if (!player) return;
            player.setVolume(e.target.value);
            if (e.target.value == 0) {{
                player.mute();
                document.getElementById('volume-icon').style.display = 'none';
                document.getElementById('mute-icon').style.display = 'block';
            }} else {{
                if (player.isMuted()) player.unMute();
                document.getElementById('volume-icon').style.display = 'block';
                document.getElementById('mute-icon').style.display = 'none';
            }}
        }});

        document.getElementById('fullscreen').addEventListener('click', () => {{
            const container = document.getElementById('video-container');
            const elem = container;
            
            // Check if already in fullscreen
            if (document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement || document.msFullscreenElement) {{
                // Exit fullscreen
                if (document.exitFullscreen) {{
                    document.exitFullscreen();
                }} else if (document.webkitExitFullscreen) {{
                    document.webkitExitFullscreen();
                }} else if (document.mozCancelFullScreen) {{
                    document.mozCancelFullScreen();
                }} else if (document.msExitFullscreen) {{
                    document.msExitFullscreen();
                }}
            }} else {{
                // Enter fullscreen with vendor prefixes for mobile support
                if (elem.requestFullscreen) {{
                    elem.requestFullscreen();
                }} else if (elem.webkitRequestFullscreen) {{
                    elem.webkitRequestFullscreen(); // Safari iOS
                }} else if (elem.webkitEnterFullscreen) {{
                    elem.webkitEnterFullscreen(); // Older iOS
                }} else if (elem.mozRequestFullScreen) {{
                    elem.mozRequestFullScreen();
                }} else if (elem.msRequestFullscreen) {{
                    elem.msRequestFullscreen();
                }}
            }}
        }});

        // Auto-hide controls
        let hideControlsTimeout;
        document.getElementById('controls-overlay').addEventListener('mousemove', () => {{
            document.getElementById('controls').classList.add('show');
            clearTimeout(hideControlsTimeout);
            hideControlsTimeout = setTimeout(() => {{
                if (isPlaying) {{
                    document.getElementById('controls').classList.remove('show');
                }}
            }}, 3000);
        }});
    </script>
</body>
</html>'''
    
    elif lesson.video_source == 'vimeo':
        video_id = extract_vimeo_video_id(lesson.video_url)
        
        if not video_id:
            return generate_error_html("Vimeo video ID not found")
        
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ height: 100%; overflow: hidden; background: #000; }}
        iframe {{ width: 100%; height: 100%; border: none; display: block; }}
    </style>
</head>
<body>
    <iframe 
        src="https://player.vimeo.com/video/{video_id}?autoplay=1"
        allowfullscreen
        allow="autoplay; fullscreen; picture-in-picture">
    </iframe>
    <script>
        document.addEventListener('contextmenu', e => e.preventDefault());
        document.addEventListener('keydown', e => {{
            if (e.keyCode === 123 || 
                (e.ctrlKey && e.shiftKey && (e.keyCode === 73 || e.keyCode === 74)) ||
                (e.ctrlKey && e.keyCode === 85)) {{
                e.preventDefault();
                return false;
            }}
        }});
    </script>
</body>
</html>'''
    
    elif lesson.video_source == 'upload' and lesson.video_file_url:
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ height: 100%; overflow: hidden; background: #000; }}
        video {{ width: 100%; height: 100%; display: block; }}
    </style>
</head>
<body>
    <video 
        src="{lesson.video_file_url}"
        controls
        autoplay
        controlsList="nodownload"
        oncontextmenu="return false;">
        Your browser does not support the video tag.
    </video>
    <script>
        document.addEventListener('contextmenu', e => e.preventDefault());
        document.addEventListener('keydown', e => {{
            if (e.keyCode === 123 || 
                (e.ctrlKey && e.shiftKey && (e.keyCode === 73 || e.keyCode === 74)) ||
                (e.ctrlKey && e.keyCode === 85)) {{
                e.preventDefault();
                return false;
            }}
        }});
    </script>
</body>
</html>'''
    
    else:
        return generate_error_html("Video source not configured")


def generate_error_html(message):
    """Generate error HTML for video player"""
    return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ height: 100%; display: flex; align-items: center; justify-content: center; background: #1a1a1a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
        .error {{ text-align: center; color: #ef4444; padding: 2rem; }}
        .error h2 {{ margin-bottom: 0.5rem; }}
        .error p {{ color: #9ca3af; }}
    </style>
</head>
<body>
    <div class="error">
        <h2>Video Not Available</h2>
        <p>{message}</p>
    </div>
</body>
</html>'''
