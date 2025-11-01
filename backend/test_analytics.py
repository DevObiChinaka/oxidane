"""
Test script for Course Analytics Phase 1 implementation
Run this from the Django shell to verify analytics service works
"""

from courses.analytics import CourseAnalyticsService
import json

def test_analytics():
    """Test all analytics methods"""
    print("🧪 Testing Course Analytics Service...")
    
    try:
        # Test course metrics
        print("\n📚 Testing Course Metrics...")
        course_metrics = CourseAnalyticsService.get_course_metrics()
        print(f"Total Courses: {course_metrics['total_courses']}")
        print(f"Published Rate: {course_metrics['publish_rate']}%")
        
        # Test content metrics  
        print("\n📝 Testing Content Metrics...")
        content_metrics = CourseAnalyticsService.get_content_metrics()
        print(f"Total Lessons: {content_metrics['total_lessons']}")
        print(f"Total Duration: {content_metrics['total_duration_hours']} hours")
        
        # Test user metrics
        print("\n👥 Testing User Metrics...")
        user_metrics = CourseAnalyticsService.get_user_metrics()
        print(f"Total Users: {user_metrics['total_users']}")
        print(f"Verification Rate: {user_metrics['verification_rate']}%")
        
        # Test popular courses
        print("\n🏆 Testing Popular Courses...")
        popular_courses = CourseAnalyticsService.get_popular_courses()
        print(f"Popular courses count: {len(popular_courses)}")
        for i, course in enumerate(popular_courses[:3]):
            print(f"{i+1}. {course['title']} ({course['lesson_count']} lessons)")
        
        # Test growth metrics
        print("\n📈 Testing Growth Metrics...")
        growth_metrics = CourseAnalyticsService.get_growth_metrics()
        print(f"Monthly course data points: {len(growth_metrics['monthly_courses'])}")
        print(f"Monthly user data points: {len(growth_metrics['monthly_users'])}")
        
        # Test full dashboard analytics
        print("\n🎯 Testing Full Dashboard Analytics...")
        dashboard_data = CourseAnalyticsService.get_dashboard_analytics()
        print(f"Dashboard data generated at: {dashboard_data['generated_at']}")
        
        print("\n✅ All analytics tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Analytics test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # This runs when executed as a script
    test_analytics()