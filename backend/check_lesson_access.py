#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from courses.models import Course, CourseAccess, Lesson
from users.models import User

# Find the test user
user = User.objects.filter(email='chiderachinaka06@gmail.com').first()
lesson_id = '9409e19a-aabe-44ca-91a2-afd4227074b8'

if user:
    print(f'User: {user.email}')
    print()
    
    # Find the lesson
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        print(f'Lesson: {lesson.title}')
        print(f'Course: {lesson.course.title}')
        print(f'Course Type: {lesson.course.course_type}')
        print()
        
        # Check enrollment
        is_enrolled = CourseAccess.objects.filter(user=user, course=lesson.course).exists()
        print(f'Is enrolled in course: {is_enrolled}')
        print()
        
        if not is_enrolled:
            print('❌ User is NOT enrolled in this course!')
            print('They need to enroll first.')
        else:
            print('✅ User is enrolled and should have access')
            
    except Lesson.DoesNotExist:
        print(f'Lesson {lesson_id} not found')
else:
    print('User not found')
