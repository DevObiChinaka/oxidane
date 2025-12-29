#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from courses.models import Course, Lesson
from courses.views import get_first_lesson_youtube_thumbnail

print("Checking courses for YouTube thumbnails...\n")
print("=" * 80)

courses = Course.objects.filter(status='published')
for course in courses:
    first_yt_lesson = course.lessons.filter(
        video_source='youtube'
    ).exclude(
        youtube_video_id=''
    ).order_by('order').first()
    
    thumbnail_data = get_first_lesson_youtube_thumbnail(course)
    
    print(f"\nCourse: {course.title}")
    print(f"  Slug: {course.slug}")
    print(f"  Has uploaded thumbnail: {bool(course.thumbnail)}")
    print(f"  Total lessons: {course.lessons.count()}")
    print(f"  YouTube lessons: {course.lessons.filter(video_source='youtube').exclude(youtube_video_id='').count()}")
    
    if first_yt_lesson:
        print(f"  First YT lesson: {first_yt_lesson.title}")
        print(f"  YT Video ID: {first_yt_lesson.youtube_video_id}")
    else:
        print(f"  First YT lesson: None")
    
    print(f"  Thumbnail data from API: {thumbnail_data}")
    
    if thumbnail_data:
        print(f"  High-res URL: {thumbnail_data['high']}")
        print(f"  Medium URL: {thumbnail_data['medium']}")
    
    print("-" * 80)
