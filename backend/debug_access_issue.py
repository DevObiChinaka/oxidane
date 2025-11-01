#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from courses.models import Course, CourseAccess, Lesson
from users.models import User
from courses.views import can_access_course

# Find the test user
user = User.objects.filter(email='chiderachinaka06@gmail.com').first()

if user:
    print(f'✅ User found: {user.email}')
    print()
    
    # Get the test course
    course = Course.objects.filter(slug='test-forex-course').first()
    
    if course:
        print(f'✅ Course found: {course.title}')
        print(f'   Course type: {course.course_type}')
        print()
        
        # Check enrollment
        enrollment = CourseAccess.objects.filter(user=user, course=course).first()
        print(f'Enrollment status: {"✅ ENROLLED" if enrollment else "❌ NOT ENROLLED"}')
        
        if enrollment:
            print(f'   Enrolled at: {enrollment.access_granted_at}')
        print()
        
        # Test can_access_course function
        has_access = can_access_course(user, course)
        print(f'can_access_course result: {"✅ TRUE (Has Access)" if has_access else "❌ FALSE (No Access)"}')
        print()
        
        if has_access:
            print('✅ User should be able to mark lessons as complete!')
        else:
            print('❌ User will get 403 error when trying to mark lessons complete')
            print('   Need to fix enrollment or access logic')
    else:
        print('Course not found')
else:
    print('User not found')
