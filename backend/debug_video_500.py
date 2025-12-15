#!/usr/bin/env python
"""
Debug video embed 500 error for premium lessons
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from courses.models import Lesson
from courses.video_views import generate_simple_embed_html
from users.models import User

# Test with the failing lesson
lesson_id = 'e0c3462e-0194-48cb-b24b-35f100f08fe3'

try:
    lesson = Lesson.objects.get(id=lesson_id)
    print(f"✓ Lesson found: {lesson.title}")
    print(f"  Course: {lesson.course.title}")
    print(f"  Video URL: {lesson.video_url}")
    print(f"  YouTube ID: {lesson.youtube_video_id}")
    print(f"  Is Preview: {lesson.is_preview}")
    print(f"  Video Source: {lesson.video_source}")
    
    # Try to generate embed HTML
    print("\n🎬 Generating embed HTML...")
    html = generate_simple_embed_html(lesson)
    print(f"✓ HTML generated successfully ({len(html)} characters)")
    
    # Test with a user
    user = User.objects.filter(email='derachinaka@gmail.com').first()
    if user:
        print(f"\n👤 Testing access for: {user.email}")
        from courses.video_security import check_user_lesson_access
        has_access = check_user_lesson_access(user, lesson)
        print(f"  Has access: {has_access}")
        
        if not has_access:
            print("  ❌ User doesn't have access to this lesson")
            print(f"  Course status: {lesson.course.status}")
            print(f"  Checking enrollments...")
            from courses.models import Enrollment
            enrollment = Enrollment.objects.filter(
                user=user,
                course=lesson.course
            ).first()
            if enrollment:
                print(f"  ✓ Enrollment found: {enrollment.status}")
            else:
                print(f"  ❌ No enrollment found for this course")
        
except Lesson.DoesNotExist:
    print(f"❌ Lesson not found: {lesson_id}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
