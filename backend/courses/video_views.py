"""
Simplified video streaming with reliable YouTube iframe embed
"""
import base64
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
        embed_html = generate_simple_embed_html(lesson)
        
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


def generate_simple_embed_html(lesson):
    """
    Generate secure embed HTML - hides video URL while using reliable YouTube iframe
    """
    if lesson.video_source == 'youtube':
        video_id = lesson.youtube_video_id or extract_youtube_video_id(lesson.video_url)
        
        if not video_id:
            return generate_error_html("YouTube video ID not found")
        
        # Direct YouTube embed - works reliably in srcDoc
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
            user-select: none;
            -webkit-user-select: none;
            position: relative;
        }}
        .video-container {{
            width: 100%;
            height: 100%;
            position: relative;
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
            display: block;
            position: absolute;
            top: 0;
            left: 0;
        }}

    </style>
</head>
<body>
    <div class="video-container" oncontextmenu="return false;">
        <iframe 
            src="https://www.youtube-nocookie.com/embed/{video_id}?autoplay=1&rel=0&modestbranding=1&playsinline=1&controls=1&showinfo=0&fs=1&iv_load_policy=3&enablejsapi=1"
            allowfullscreen
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            frameborder="0"
            oncontextmenu="return false;">
        </iframe>
    </div>

    <script>
        // Security: Aggressive right-click blocking
        function blockContextMenu(e) {{
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            return false;
        }}

        // Apply to document
        document.addEventListener('contextmenu', blockContextMenu, true);
        document.addEventListener('contextmenu', blockContextMenu, false);
        
        // Apply to body
        document.body.addEventListener('contextmenu', blockContextMenu, true);
        document.body.addEventListener('contextmenu', blockContextMenu, false);
        
        // Apply to video container
        const container = document.querySelector('.video-container');
        if (container) {{
            container.addEventListener('contextmenu', blockContextMenu, true);
            container.addEventListener('contextmenu', blockContextMenu, false);
            container.oncontextmenu = blockContextMenu;
        }}

        // Apply to iframe when loaded
        const iframe = document.querySelector('iframe');
        if (iframe) {{
            iframe.addEventListener('contextmenu', blockContextMenu, true);
            iframe.addEventListener('contextmenu', blockContextMenu, false);
            iframe.oncontextmenu = blockContextMenu;
            
            // Also try to block after iframe loads
            iframe.addEventListener('load', () => {{
                try {{
                    iframe.contentWindow.document.addEventListener('contextmenu', blockContextMenu, true);
                }} catch(e) {{
                    // Cross-origin, can't access
                }}
            }});
        }}

        // Security: Disable DevTools shortcuts
        document.addEventListener('keydown', e => {{
            if (e.keyCode === 123 || 
                (e.ctrlKey && e.shiftKey && (e.keyCode === 73 || e.keyCode === 74)) ||
                (e.ctrlKey && e.keyCode === 85) ||
                (e.ctrlKey && e.keyCode === 83)) {{
                e.preventDefault();
                e.stopPropagation();
                return false;
            }}
        }}, true);

        // Prevent text selection
        document.body.style.userSelect = 'none';
        document.body.style.webkitUserSelect = 'none';
        document.body.style.webkitTouchCallout = 'none';
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
