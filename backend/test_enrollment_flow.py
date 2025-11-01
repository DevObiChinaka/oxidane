#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from courses.models import Course, CourseAccess
from users.models import User

# Find the test user
user = User.objects.filter(email='chiderachinaka06@gmail.com').first()

if user:
    print(f'Testing enrollment flow for: {user.email}')
    print()
    
    # Get a free course
    free_course = Course.objects.filter(status='published', course_type='free').first()
    
    if free_course:
        print(f'Testing with course: {free_course.title}')
        print(f'Course type: {free_course.course_type}')
        print(f'Course slug: {free_course.slug}')
        print()
        
        # Check current enrollment
        is_enrolled = CourseAccess.objects.filter(user=user, course=free_course).exists()
        print(f'Currently enrolled: {is_enrolled}')
        
        # Simulate the can_access_course function
        if free_course.course_type == 'free':
            can_access = CourseAccess.objects.filter(user=user, course=free_course).exists()
        else:
            can_access = False
        
        print(f'Can access: {can_access}')
        print(f'Should show Enroll button: {not is_enrolled and not can_access}')
        print(f'Should show Start Learning: {is_enrolled and can_access}')
        print()
        
        if not is_enrolled:
            print('✅ Correct! User should see "Enroll Now" button')
        else:
            print('❌ User is already enrolled - should see "Start Learning" button')
    else:
        print('No free courses found')
else:
    print('User not found')
