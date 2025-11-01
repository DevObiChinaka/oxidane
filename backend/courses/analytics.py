# Course Analytics Service
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import Course, Lesson

User = get_user_model()

class CourseAnalyticsService:
    """Service class for generating course analytics data"""
    
    @staticmethod
    def get_course_metrics():
        """Get core course metrics"""
        total_courses = Course.objects.count()
        published_courses = Course.objects.filter(status='published').count()
        draft_courses = Course.objects.filter(status='draft').count()
        archived_courses = Course.objects.filter(status='archived').count()
        
        # Course type distribution
        free_courses = Course.objects.filter(course_type='free').count()
        premium_courses = Course.objects.filter(course_type='premium').count()
        
        # Difficulty distribution
        difficulty_stats = Course.objects.values('difficulty_level').annotate(
            count=models.Count('id')
        ).order_by('difficulty_level')
        
        return {
            'total_courses': total_courses,
            'published_courses': published_courses,
            'draft_courses': draft_courses,
            'archived_courses': archived_courses,
            'free_courses': free_courses,
            'premium_courses': premium_courses,
            'difficulty_distribution': list(difficulty_stats),
            'publish_rate': round((published_courses / total_courses * 100), 1) if total_courses > 0 else 0
        }
    
    @staticmethod
    def get_content_metrics():
        """Get content-related metrics"""
        total_lessons = Lesson.objects.count()
        total_duration = Lesson.objects.aggregate(
            total=models.Sum('duration')
        )['total'] or 0
        
        # Convert minutes to hours for better display
        total_hours = round(total_duration / 60, 1)
        
        # Average lessons per course
        courses_with_lessons = Course.objects.filter(lessons__isnull=False).distinct().count()
        avg_lessons_per_course = round(total_lessons / courses_with_lessons, 1) if courses_with_lessons > 0 else 0
        
        # Preview content stats
        preview_lessons = Lesson.objects.filter(is_preview=True).count()
        preview_percentage = round((preview_lessons / total_lessons * 100), 1) if total_lessons > 0 else 0
        
        return {
            'total_lessons': total_lessons,
            'total_duration_minutes': total_duration,
            'total_duration_hours': total_hours,
            'avg_lessons_per_course': avg_lessons_per_course,
            'preview_lessons': preview_lessons,
            'preview_percentage': preview_percentage
        }
    
    @staticmethod
    def get_user_metrics():
        """Get user engagement metrics"""
        total_users = User.objects.count()
        verified_users = User.objects.filter(is_email_verified=True).count()
        active_users = User.objects.filter(is_active=True).count()
        
        # Recent registration trends (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_registrations = User.objects.filter(created_at__gte=thirty_days_ago).count()
        
        # Weekly registration trend (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        weekly_registrations = User.objects.filter(created_at__gte=seven_days_ago).count()
        
        verification_rate = round((verified_users / total_users * 100), 1) if total_users > 0 else 0
        
        return {
            'total_users': total_users,
            'verified_users': verified_users,
            'active_users': active_users,
            'recent_registrations_30d': recent_registrations,
            'recent_registrations_7d': weekly_registrations,
            'verification_rate': verification_rate
        }
    
    @staticmethod
    def get_popular_courses():
        """Get popular courses based on lesson count and recent activity"""
        # For Phase 1, we'll rank by total lessons and duration
        # In future phases, we can add view counts, enrollment data
        popular_courses = Course.objects.filter(
            status='published'
        ).annotate(
            lesson_count=models.Count('lessons'),
            total_lesson_duration=models.Sum('lessons__duration')
        ).order_by('-lesson_count', '-total_lesson_duration')[:5]
        
        return [{
            'id': str(course.id),
            'title': course.title,
            'slug': course.slug,
            'course_type': course.course_type,
            'difficulty_level': course.difficulty_level,
            'lesson_count': course.lesson_count,
            'total_duration': course.total_lesson_duration or 0,
            'created_at': course.created_at.isoformat(),
            'published_at': course.published_at.isoformat() if course.published_at else None
        } for course in popular_courses]
    
    @staticmethod
    def get_growth_metrics():
        """Get enhanced growth metrics with accurate calculations and trends"""
        from datetime import datetime
        from calendar import monthrange
        
        now = timezone.now()
        current_year = now.year
        current_month = now.month
        
        # Get 12 months of accurate data (including current month)
        monthly_courses = []
        monthly_users = []
        
        for i in range(12):
            # Calculate exact month boundaries
            target_year = current_year
            target_month = current_month - i
            
            if target_month <= 0:
                target_month += 12
                target_year -= 1
            
            # Get first and last day of the month
            month_start = datetime(target_year, target_month, 1, tzinfo=now.tzinfo)
            last_day = monthrange(target_year, target_month)[1]
            month_end = datetime(target_year, target_month, last_day, 23, 59, 59, tzinfo=now.tzinfo)
            
            # Course count for this month
            courses_count = Course.objects.filter(
                created_at__gte=month_start,
                created_at__lte=month_end
            ).count()
            
            # User count for this month  
            users_count = User.objects.filter(
                created_at__gte=month_start,
                created_at__lte=month_end
            ).count()
            
            month_label = month_start.strftime('%Y-%m')
            month_name = month_start.strftime('%b %Y')
            
            monthly_courses.append({
                'month': month_label,
                'month_name': month_name,
                'courses': courses_count,
                'year': target_year,
                'month_number': target_month
            })
            
            monthly_users.append({
                'month': month_label,
                'month_name': month_name,
                'users': users_count,
                'year': target_year,
                'month_number': target_month
            })
        
        # Reverse to show oldest to newest
        monthly_courses.reverse()
        monthly_users.reverse()
        
        # Calculate growth rates and trends
        def calculate_growth_metrics(data, metric_key):
            enhanced_data = []
            for i, item in enumerate(data):
                growth_rate = 0
                growth_direction = 'neutral'
                
                if i > 0:  # Calculate month-over-month growth
                    prev_value = data[i-1][metric_key]
                    current_value = item[metric_key]
                    
                    if prev_value > 0:
                        growth_rate = ((current_value - prev_value) / prev_value) * 100
                        growth_direction = 'up' if growth_rate > 0 else ('down' if growth_rate < 0 else 'neutral')
                    elif current_value > 0:
                        growth_rate = 100  # From 0 to something is 100% growth
                        growth_direction = 'up'
                
                enhanced_data.append({
                    **item,
                    'growth_rate': round(growth_rate, 1),
                    'growth_direction': growth_direction
                })
            
            return enhanced_data
        
        enhanced_courses = calculate_growth_metrics(monthly_courses, 'courses')
        enhanced_users = calculate_growth_metrics(monthly_users, 'users')
        
        # Calculate overall trends (last 3 months vs previous 3 months)
        def calculate_trend_summary(data, metric_key):
            if len(data) < 6:
                return {'trend': 'neutral', 'percentage': 0}
                
            recent_period = sum(item[metric_key] for item in data[-3:])
            previous_period = sum(item[metric_key] for item in data[-6:-3])
            
            if previous_period == 0:
                return {'trend': 'up' if recent_period > 0 else 'neutral', 'percentage': 0}
            
            change_percentage = ((recent_period - previous_period) / previous_period) * 100
            return {
                'trend': 'up' if change_percentage > 5 else ('down' if change_percentage < -5 else 'neutral'),
                'percentage': round(change_percentage, 1)
            }
        
        course_trend = calculate_trend_summary(enhanced_courses, 'courses')
        user_trend = calculate_trend_summary(enhanced_users, 'users')
        
        return {
            'monthly_courses': enhanced_courses,
            'monthly_users': enhanced_users,
            'course_trend_summary': course_trend,
            'user_trend_summary': user_trend,
            'total_months': len(enhanced_courses)
        }
    
    @classmethod
    def get_dashboard_analytics(cls):
        """Get all analytics data for dashboard"""
        return {
            'course_metrics': cls.get_course_metrics(),
            'content_metrics': cls.get_content_metrics(),
            'user_metrics': cls.get_user_metrics(),
            'popular_courses': cls.get_popular_courses(),
            'growth_metrics': cls.get_growth_metrics(),
            'generated_at': timezone.now().isoformat()
        }