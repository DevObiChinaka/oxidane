#!/usr/bin/env python
"""Create default course categories"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from courses.models import CourseCategory
from django.utils.text import slugify

def create_default_categories():
    """Create default course categories"""
    
    print("=" * 80)
    print("📚 Creating Default Course Categories")
    print("=" * 80)
    print()
    
    categories = [
        {
            'name': 'Forex Fundamentals',
            'description': 'Learn the basics of forex trading, currency pairs, and market structure',
            'icon': '📊',
            'order': 1
        },
        {
            'name': 'Technical Analysis',
            'description': 'Master chart patterns, indicators, and technical trading strategies',
            'icon': '📈',
            'order': 2
        },
        {
            'name': 'Risk Management',
            'description': 'Protect your capital with proper risk management and position sizing',
            'icon': '🛡️',
            'order': 3
        },
        {
            'name': 'Trading Psychology',
            'description': 'Develop the mindset and discipline needed for successful trading',
            'icon': '🧠',
            'order': 4
        },
        {
            'name': 'Trading Strategies',
            'description': 'Complete trading systems and strategies for different market conditions',
            'icon': '⚡',
            'order': 5
        },
        {
            'name': 'Price Action',
            'description': 'Trade naked charts using pure price action and market structure',
            'icon': '📉',
            'order': 6
        },
        {
            'name': 'Advanced Trading',
            'description': 'Advanced concepts for experienced traders including algo trading',
            'icon': '🚀',
            'order': 7
        }
    ]
    
    created_count = 0
    existing_count = 0
    
    for cat_data in categories:
        slug = slugify(cat_data['name'])
        
        category, created = CourseCategory.objects.get_or_create(
            slug=slug,
            defaults={
                'name': cat_data['name'],
                'description': cat_data['description'],
                'icon': cat_data['icon'],
                'order': cat_data['order']
            }
        )
        
        if created:
            print(f"✅ Created: {category.name} ({category.icon})")
            created_count += 1
        else:
            print(f"ℹ️  Already exists: {category.name}")
            existing_count += 1
    
    print()
    print("=" * 80)
    print(f"✨ Summary: Created {created_count} new categories, {existing_count} already existed")
    print("=" * 80)
    print()
    print("📋 All Categories:")
    for cat in CourseCategory.objects.all().order_by('order'):
        print(f"   {cat.order}. {cat.icon} {cat.name}")
        print(f"      Slug: {cat.slug}")
        print(f"      Courses: {cat.course_count}")
        print()

if __name__ == '__main__':
    create_default_categories()
