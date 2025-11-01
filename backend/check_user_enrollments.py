#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from courses.models import CourseAccess, Course
from users.models import User

# Find the test user
user = User.objects.filter(email='chiderachinaka06@gmail.com').first()

if user:
    print(f'User found: {user.email}')
    print(f'User ID: {user.id}')
    print(f'Username: {user.username}')
    print()
    
    # Check enrollments
    enrollments = CourseAccess.objects.filter(user=user)
    print(f'Total Enrollments: {enrollments.count()}')
    print()
    
    if enrollments.exists():
        print('Enrolled Courses:')
        for enrollment in enrollments:
            print(f'  - {enrollment.course.title}')
            print(f'    Course Type: {enrollment.course.course_type}')
            print(f'    Enrolled At: {enrollment.access_granted_at}')
            print()
    else:
        print('No enrollments found for this user.')
        print()
        print('Available Free Courses:')
        free_courses = Course.objects.filter(status='published', course_type='free')
        for course in free_courses:
            print(f'  - {course.title} (slug: {course.slug})')
else:
    print('User not found: chiderachinaka06@gmail.com')
    print()
    print('Available users:')
    for u in User.objects.all()[:5]:
        print(f'  - {u.email}')
