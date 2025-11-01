#!/usr/bin/env python
"""List all courses and their structure"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from courses.models import Course, Lesson, CourseProgress, LessonProgress, CourseAccess
from django.contrib.auth import get_user_model

User = get_user_model()

def display_course_structure():
    """Display complete course structure"""
    
    print("=" * 80)
    print("📚 OXIDANE COURSES - COMPLETE STRUCTURE")
    print("=" * 80)
    print()
    
    # Get all courses
    courses = Course.objects.all().order_by('order', 'created_at')
    
    if not courses:
        print("❌ No courses found in the database.")
        return
    
    print(f"📊 Total Courses: {courses.count()}\n")
    
    for idx, course in enumerate(courses, 1):
        print(f"{'='*80}")
        print(f"Course #{idx}: {course.title}")
        print(f"{'='*80}")
        print(f"  ID: {course.id}")
        print(f"  Slug: {course.slug}")
        print(f"  Type: {course.get_course_type_display()}")
        print(f"  Difficulty: {course.get_difficulty_level_display()}")
        print(f"  Status: {course.get_status_display()}")
        print(f"  Order: {course.order}")
        print(f"  Estimated Duration: {course.estimated_duration} minutes")
        print(f"  Created: {course.created_at.strftime('%Y-%m-%d %H:%M')}")
        
        if course.published_at:
            print(f"  Published: {course.published_at.strftime('%Y-%m-%d %H:%M')}")
        
        print(f"\n  Description:")
        print(f"    {course.short_description}")
        
        if course.thumbnail:
            print(f"\n  Thumbnail: {course.thumbnail.url}")
        
        if course.trailer_video_url:
            print(f"  Trailer: {course.trailer_video_url}")
        
        # SEO Info
        if course.meta_title or course.meta_description or course.keywords:
            print(f"\n  SEO Information:")
            if course.meta_title:
                print(f"    Meta Title: {course.meta_title}")
            if course.meta_description:
                print(f"    Meta Description: {course.meta_description}")
            if course.keywords:
                print(f"    Keywords: {course.keywords}")
        
        # Get lessons
        lessons = course.lessons.all().order_by('order')
        print(f"\n  📝 Lessons ({lessons.count()}):")
        
        if lessons:
            for lesson_idx, lesson in enumerate(lessons, 1):
                print(f"    {lesson_idx}. {lesson.title}")
                print(f"       - Order: {lesson.order}")
                print(f"       - Duration: {lesson.duration} minutes")
                print(f"       - Video Source: {lesson.get_video_source_display()}")
                print(f"       - Is Preview: {'Yes' if lesson.is_preview else 'No'}")
                
                if lesson.video_url:
                    print(f"       - Video URL: {lesson.video_url}")
                if lesson.youtube_video_id:
                    print(f"       - YouTube ID: {lesson.youtube_video_id}")
                if lesson.video_file:
                    print(f"       - Video File: {lesson.video_file.name}")
                
                print()
        else:
            print("    No lessons yet")
        
        # Check enrollments
        access_count = CourseAccess.objects.filter(course=course).count()
        if access_count > 0:
            print(f"  👥 Enrolled Users: {access_count}")
        
        # Check progress
        progress_count = CourseProgress.objects.filter(course=course).count()
        if progress_count > 0:
            print(f"  📈 Users with Progress: {progress_count}")
        
        print("\n")
    
    # Summary statistics
    print("=" * 80)
    print("📊 SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Total Courses: {courses.count()}")
    print(f"  - Free Courses: {courses.filter(course_type='free').count()}")
    print(f"  - Premium Courses: {courses.filter(course_type='premium').count()}")
    print(f"  - Published: {courses.filter(status='published').count()}")
    print(f"  - Draft: {courses.filter(status='draft').count()}")
    print(f"  - Archived: {courses.filter(status='archived').count()}")
    print(f"\nTotal Lessons: {Lesson.objects.count()}")
    print(f"Total Users with Course Access: {CourseAccess.objects.count()}")
    print(f"Total Course Progress Records: {CourseProgress.objects.count()}")
    print(f"Total Lesson Progress Records: {LessonProgress.objects.count()}")
    print()

if __name__ == '__main__':
    display_course_structure()
