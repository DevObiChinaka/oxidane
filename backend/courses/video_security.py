"""
Video security utilities for secure video streaming
"""
import secrets
import hashlib
import re
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache


def generate_video_access_token(user_id, lesson_id, expires_hours=6):
    """
    Generate a secure access token for video streaming
    
    Args:
        user_id: UUID of the user
        lesson_id: UUID of the lesson
        expires_hours: Token expiration time in hours (default: 6)
    
    Returns:
        tuple: (token, expires_at)
    """
    # Create a unique token combining random bytes with user/lesson data
    random_part = secrets.token_urlsafe(32)
    data_part = f"{user_id}:{lesson_id}:{timezone.now().timestamp()}"
    
    # Hash the combination for security
    token = hashlib.sha256(f"{random_part}:{data_part}".encode()).hexdigest()
    
    # Calculate expiration
    expires_at = timezone.now() + timedelta(hours=expires_hours)
    
    return token, expires_at


def verify_video_access_token(token):
    """
    Verify a video access token
    
    Args:
        token: The access token to verify
    
    Returns:
        VideoAccessLog instance if valid, None otherwise
    """
    from .models import VideoAccessLog
    
    try:
        access_log = VideoAccessLog.objects.get(access_token=token)
        
        if access_log.is_valid():
            return access_log
        else:
            return None
            
    except VideoAccessLog.DoesNotExist:
        return None


def extract_youtube_video_id(url):
    """
    Extract YouTube video ID from various URL formats
    
    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/v/VIDEO_ID
    
    Args:
        url: YouTube URL string
    
    Returns:
        str: Video ID if found, None otherwise
    """
    if not url:
        return None
    
    # Pattern for various YouTube URL formats
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # If it's already just the ID (11 characters)
    if len(url) == 11 and re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    
    return None


def extract_vimeo_video_id(url):
    """
    Extract Vimeo video ID from URL
    
    Args:
        url: Vimeo URL string
    
    Returns:
        str: Video ID if found, None otherwise
    """
    if not url:
        return None
    
    # Pattern for Vimeo URLs
    pattern = r'vimeo\.com\/(\d+)'
    match = re.search(pattern, url)
    
    if match:
        return match.group(1)
    
    # If it's already just numeric ID
    if url.isdigit():
        return url
    
    return None


def check_user_lesson_access(user, lesson):
    """
    Check if user has access to a specific lesson
    
    Args:
        user: User instance
        lesson: Lesson instance
    
    Returns:
        bool: True if user has access, False otherwise
    """
    course = lesson.course
    
    # Check if course is published
    if course.status != 'published':
        return False
    
    # If lesson is marked as preview, everyone can access
    if lesson.is_preview:
        return True
    
    # Check course access
    return course.is_accessible_by_user(user)


def get_client_ip(request):
    """
    Get the client's IP address from request
    
    Args:
        request: Django request object
    
    Returns:
        str: IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def revoke_user_video_tokens(user, lesson=None):
    """
    Revoke all active video tokens for a user
    
    Args:
        user: User instance
        lesson: Optional Lesson instance to revoke tokens for specific lesson only
    """
    from .models import VideoAccessLog
    
    query = VideoAccessLog.objects.filter(user=user, is_active=True)
    
    if lesson:
        query = query.filter(lesson=lesson)
    
    query.update(is_active=False)


def cleanup_expired_tokens():
    """
    Clean up expired video access tokens
    Should be run periodically (e.g., daily via cron job)
    
    Returns:
        int: Number of tokens cleaned up
    """
    from .models import VideoAccessLog
    
    expired_tokens = VideoAccessLog.objects.filter(
        expires_at__lt=timezone.now(),
        is_active=True
    )
    
    count = expired_tokens.count()
    expired_tokens.update(is_active=False)
    
    return count


def get_user_active_sessions(user, lesson=None):
    """
    Get count of active video sessions for a user
    
    Args:
        user: User instance
        lesson: Optional Lesson instance to filter by specific lesson
    
    Returns:
        int: Number of active sessions
    """
    from .models import VideoAccessLog
    
    query = VideoAccessLog.objects.filter(
        user=user,
        is_active=True,
        expires_at__gt=timezone.now()
    )
    
    if lesson:
        query = query.filter(lesson=lesson)
    
    return query.count()


def detect_suspicious_activity(user, lesson):
    """
    Detect suspicious video access patterns
    
    Args:
        user: User instance
        lesson: Lesson instance
    
    Returns:
        dict: {
            'is_suspicious': bool,
            'reasons': list of reason strings,
            'metrics': dict of relevant metrics
        }
    """
    from .models import VideoAccessLog
    from django.db.models import Count
    
    reasons = []
    
    # Check 1: Too many active sessions
    active_sessions = get_user_active_sessions(user, lesson)
    if active_sessions > 3:
        reasons.append(f"Too many concurrent sessions ({active_sessions})")
    
    # Check 2: Multiple IPs in short time
    recent_logs = VideoAccessLog.objects.filter(
        user=user,
        lesson=lesson,
        created_at__gte=timezone.now() - timedelta(hours=1)
    )
    
    unique_ips = recent_logs.values('ip_address').distinct().count()
    if unique_ips > 3:
        reasons.append(f"Multiple IPs in 1 hour ({unique_ips} different IPs)")
    
    # Check 3: Excessive token generation
    tokens_today = VideoAccessLog.objects.filter(
        user=user,
        lesson=lesson,
        created_at__gte=timezone.now() - timedelta(days=1)
    ).count()
    
    if tokens_today > 20:
        reasons.append(f"Excessive token requests ({tokens_today} in 24h)")
    
    return {
        'is_suspicious': len(reasons) > 0,
        'reasons': reasons,
        'metrics': {
            'active_sessions': active_sessions,
            'unique_ips_1h': unique_ips,
            'tokens_24h': tokens_today
        }
    }
