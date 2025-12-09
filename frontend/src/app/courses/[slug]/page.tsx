'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import DashboardSidebar from '@/app/components/DashboardSidebar';
import { apiGet, apiPost } from '@/lib/api';

interface Lesson {
  id: string;
  title: string;
  description: string;
  video_source: 'upload' | 'youtube' | 'vimeo';
  video_url?: string;
  video_file_url?: string;  // For uploaded videos
  youtube_video_id?: string;
  vimeo_video_id?: string;
  duration: string;
  order: number;
  is_preview: boolean;
  is_completed?: boolean;
}

interface CourseDetail {
  id: string;
  title: string;
  slug: string;
  short_description: string;
  description: string;
  thumbnail?: string;
  first_lesson_thumbnail?: {
    high: string;
    medium: string;
  } | null;
  trailer_video_url?: string;
  course_type: 'free' | 'premium';
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
  estimated_duration: string;
  total_lessons: number;
  is_enrolled: boolean;
  can_access: boolean;
  requires_subscription: boolean;
  progress_percentage?: number;
  lessons_completed?: number;
  lessons: Lesson[];
}

export default function CourseDetailPage() {
  const router = useRouter();
  const params = useParams();
  const slug = params?.slug as string;

  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [enrolling, setEnrolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [expandedLessons, setExpandedLessons] = useState(true); // For collapsible lesson list

  useEffect(() => {
    if (slug) {
      checkAuthAndFetchCourse();
    }
  }, [slug]);

  const checkAuthAndFetchCourse = async () => {
    try {
      // Verify token is valid
      const profileResponse = await apiGet('/auth/profile/');

      if (!profileResponse.ok) {
        return;
      }

      setIsAuthenticated(true);
      await fetchCourseDetail();
    } catch (error) {
      console.error('Auth check failed:', error);
    }
  };

  const fetchCourseDetail = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiGet(`/courses/${slug}/`);

      if (response.ok) {
        const data = await response.json();
        
        // Transform the response to match our interface
        const transformedData = {
          ...data,
          // Map progress data to top level
          progress_percentage: data.progress?.completion_percentage || 0,
          lessons_completed: data.progress?.lessons_completed || 0,
          // Transform lessons to use is_completed instead of completed
          lessons: data.lessons.map((lesson: any) => ({
            ...lesson,
            is_completed: lesson.completed || false,
          })),
        };
        
        setCourse(transformedData);
      } else if (response.status === 404) {
        setError('Course not found');
      } else {
        setError('Failed to load course details');
      }
    } catch (err) {
      console.error('Error fetching course:', err);
      setError('Failed to load course details');
    } finally {
      setLoading(false);
    }
  };

  const handleEnroll = async () => {
    const token = localStorage.getItem('user_auth_token') || localStorage.getItem('access_token');
    if (!token) {
      router.push('/auth');
      return;
    }

    if (course?.course_type === 'premium' && course?.requires_subscription) {
      router.push('/pricing');
      return;
    }

    try {
      setEnrolling(true);
      setError(null); // Clear any previous errors
      const response = await apiPost(`/courses/${slug}/enroll/`);

      if (response.ok) {
        const data = await response.json();

        setSuccessMessage(data.message || 'Successfully enrolled in course!');
        setTimeout(() => setSuccessMessage(null), 1500);
        // Redirect to My Courses so user sees it added
        setTimeout(() => router.push('/my-courses'), 1600);
      } else {
        const data = await response.json();
        console.error('Enrollment failed:', data);
        setError(data.error || 'Failed to enroll in course');
      }
    } catch (err) {
      setError('Failed to enroll in course. Please try again.');
    } finally {
      setEnrolling(false);
    }
  };

  const handleStartLearning = () => {
    if (course && course.lessons.length > 0) {
      // Find the first incomplete lesson, or default to the first lesson
      const firstIncomplete = course.lessons.find(l => !l.is_completed);
      const targetLesson = firstIncomplete || course.lessons[0];
      router.push(`/courses/${course.slug}/watch?lesson=${targetLesson.id}`);
    }
  };

  const getDifficultyColor = (level: string) => {
    switch (level) {
      case 'beginner':
        return 'bg-gray-100 text-gray-700 border-gray-200';
      case 'intermediate':
        return 'bg-gray-100 text-gray-700 border-gray-200';
      case 'advanced':
        return 'bg-gray-100 text-gray-700 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getVideoEmbedUrl = (lesson: Lesson) => {
    if (lesson.video_source === 'youtube' && lesson.youtube_video_id) {
      return `https://www.youtube.com/embed/${lesson.youtube_video_id}?enablejsapi=1&start=0`;
    } else if (lesson.video_source === 'vimeo' && lesson.vimeo_video_id) {
      return `https://player.vimeo.com/video/${lesson.vimeo_video_id}`;
    }
    return lesson.video_url || '';
  };

  const getVideoThumbnail = (lesson: Lesson) => {
    // YouTube thumbnail
    if (lesson.video_source === 'youtube' && lesson.youtube_video_id) {
      return `https://img.youtube.com/vi/${lesson.youtube_video_id}/mqdefault.jpg`;
    }
    // Vimeo thumbnail would require API call, so return null for now
    // For uploaded videos, return null (will show placeholder)
    return null;
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <DashboardSidebar 
          isMobileMenuOpen={isMobileMenuOpen}
          setIsMobileMenuOpen={setIsMobileMenuOpen}
        />
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#00B38F]"></div>
        </div>
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <DashboardSidebar 
          isMobileMenuOpen={isMobileMenuOpen}
          setIsMobileMenuOpen={setIsMobileMenuOpen}
        />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">{error || 'Course not found'}</h2>
            <button
              onClick={() => router.push('/courses')}
              className="px-6 py-3 bg-[#00B38F] hover:bg-[#00A87D] text-white rounded-lg transition-all"
            >
              Back to Courses
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <DashboardSidebar 
        isMobileMenuOpen={isMobileMenuOpen}
        setIsMobileMenuOpen={setIsMobileMenuOpen}
      />

      {/* Main Content */}
      <main className="flex-1 min-h-screen">
        {/* Mobile Menu Button */}
        <div className="lg:hidden fixed top-4 left-4 z-30">
          <button
            onClick={() => setIsMobileMenuOpen(true)}
            className="p-2 rounded-lg bg-white border border-gray-200 shadow-sm hover:bg-gray-50"
          >
            <svg className="w-6 h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>

          {/* Success Toast */}
      {successMessage && (
        <div className="fixed top-6 right-6 z-50 animate-slide-in-right">
          <div className="bg-white border-l-4 border-emerald-500 shadow-xl rounded-lg px-6 py-4 flex items-center space-x-3 max-w-md">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
            <div className="flex-1">
              <p className="font-semibold text-gray-900">{successMessage}</p>
            </div>
          </div>
        </div>
      )}

      {/* Error Toast */}
      {error && (
        <div className="fixed top-6 right-6 z-50 animate-slide-in-right">
          <div className="bg-white border-l-4 border-rose-500 shadow-xl rounded-lg px-6 py-4 flex items-center space-x-3 max-w-md">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 bg-rose-100 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="flex-1">
              <p className="font-semibold text-gray-900">{error}</p>
            </div>
            <button onClick={() => setError(null)} className="text-gray-400 hover:text-gray-600 transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Content Wrapper */}
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Back Navigation */}
          <div>
            <button
              onClick={() => router.push('/courses')}
              className="inline-flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors ml-12 lg:ml-0"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              <span className="font-medium">Back to Courses</span>
            </button>
          </div>

      {/* Course Header */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6 lg:p-8 mb-4 sm:mb-6">
        <div className="flex flex-col gap-4 sm:gap-6">
          <div className="flex-1">
            <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-900 mb-2 sm:mb-3">{course.title}</h1>
            <p className="text-sm sm:text-base text-gray-600 leading-relaxed mb-3 sm:mb-4">{course.short_description}</p>
            
            {/* Course Meta */}
            <div className="flex flex-wrap gap-3 sm:gap-4 text-xs sm:text-sm">
              <div className="flex items-center gap-2">
                <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <span className="text-gray-700">{course.total_lessons} lessons</span>
              </div>
              <div className="flex items-center gap-2">
                <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-gray-700">{course.estimated_duration}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded border border-gray-200">
                  {course.difficulty_level}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded border border-gray-200">
                  {course.course_type}
                </span>
              </div>
            </div>
          </div>

          {/* CTA Section */}
          <div className="w-full">
            {course.can_access ? (
              <button
                onClick={handleStartLearning}
                className="w-full px-4 sm:px-6 py-2.5 sm:py-3 bg-[#00B38F] hover:bg-[#00A87D] text-white rounded-lg transition-all font-medium text-sm sm:text-base"
              >
                {course.is_enrolled ? 'Continue Learning' : 'Start Learning'}
              </button>
            ) : course.requires_subscription ? (
              <div className="space-y-2 sm:space-y-3">
                <p className="text-xs sm:text-sm text-gray-600 text-center">Requires mentorship subscription</p>
                <button
                  onClick={() => router.push('/pricing')}
                  className="w-full px-4 sm:px-6 py-2.5 sm:py-3 bg-gray-900 hover:bg-gray-800 text-white rounded-lg transition-all font-medium text-sm sm:text-base"
                >
                  Upgrade to Premium
                </button>
              </div>
            ) : (
              <button
                onClick={handleEnroll}
                disabled={enrolling}
                className="w-full px-4 sm:px-6 py-2.5 sm:py-3 bg-[#00B38F] hover:bg-[#00A87D] text-white rounded-lg transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
              >
                {enrolling ? 'Enrolling...' : 'Enroll for Free'}
              </button>
            )}
          </div>
        </div>

        {/* Progress Bar (if enrolled) */}
        {course.is_enrolled && course.progress_percentage !== undefined && (
          <div className="mt-4 sm:mt-6 pt-4 sm:pt-6 border-t border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs sm:text-sm font-medium text-gray-700">Your Progress</span>
              <span className="text-sm sm:text-base font-semibold text-gray-900">{course.progress_percentage}%</span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-[#00B38F] rounded-full transition-all duration-500"
                style={{ width: `${course.progress_percentage}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {course.lessons_completed} of {course.total_lessons} lessons completed
            </p>
          </div>
        )}
      </div>

      {/* About Course */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6 lg:p-8 mb-4 sm:mb-6">
        <h2 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">About This Course</h2>
        <p className="text-sm sm:text-base text-gray-600 leading-relaxed whitespace-pre-line">{course.description}</p>
      </div>

      {/* Course Content */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6 lg:p-8">
        <div className="flex items-center justify-between mb-4 sm:mb-6">
          <h2 className="text-base sm:text-lg font-semibold text-gray-900">Course Curriculum</h2>
          <button
            onClick={() => setExpandedLessons(!expandedLessons)}
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            <span>{expandedLessons ? 'Collapse' : 'Expand'}</span>
            <svg 
              className={`w-4 h-4 transition-transform ${expandedLessons ? 'rotate-180' : ''}`} 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>

        {expandedLessons && (
          <div className="space-y-2">
            {course.lessons.length > 0 ? (
              course.lessons.map((lesson) => (
                <div
                  key={lesson.id}
                  className={`group rounded-lg border transition-all ${
                    lesson.is_completed
                      ? 'bg-gray-50 border-gray-200'
                      : 'bg-white border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="p-3 sm:p-4">
                    <div className="flex items-start gap-2 sm:gap-3 md:gap-4">
                      {/* Lesson Thumbnail/Icon */}
                      <div className="flex-shrink-0 w-20 h-12 sm:w-28 sm:h-16 md:w-32 md:h-20 bg-gray-900 rounded-md sm:rounded-lg border border-gray-300 sm:border-2 flex items-center justify-center relative overflow-hidden group-hover:border-[#00B38F] group-hover:shadow-md transition-all">
                        {getVideoThumbnail(lesson) ? (
                          <>
                            <img 
                              src={getVideoThumbnail(lesson)!} 
                              alt={lesson.title}
                              className="absolute inset-0 w-full h-full object-cover"
                            />
                            <div className="absolute inset-0 bg-black/20 group-hover:bg-black/10 transition-all"></div>
                            <svg className="w-8 h-8 sm:w-10 sm:h-10 md:w-12 md:h-12 text-white relative z-10 drop-shadow-lg group-hover:scale-110 transition-transform" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                            </svg>
                          </>
                        ) : (
                          <>
                            <div className="absolute inset-0 bg-gradient-to-br from-gray-200 via-gray-100 to-gray-50"></div>
                            <div className="absolute inset-0 bg-gradient-to-br from-[#00B38F]/10 to-transparent"></div>
                            <svg className="w-8 h-8 sm:w-10 sm:h-10 md:w-12 md:h-12 text-gray-500 relative z-10 group-hover:text-[#00B38F] transition-colors" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                            </svg>
                          </>
                        )}
                      </div>

                      {/* Lesson Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2 sm:gap-4 mb-1 sm:mb-2">
                          <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                            <span className="text-xs font-medium text-gray-500">Lesson {lesson.order}</span>
                            {lesson.is_completed && (
                              <span className="px-1.5 sm:px-2 py-0.5 bg-gray-200 text-gray-700 text-xs rounded">
                                Completed
                              </span>
                            )}
                            <span className="text-xs text-gray-500">{lesson.duration}</span>
                          </div>
                        </div>
                        <h3 className="text-xs sm:text-sm font-medium text-gray-900 mb-0.5 sm:mb-1 group-hover:text-[#00B38F] transition-colors line-clamp-2">
                          {lesson.title}
                        </h3>
                        {(course.can_access || lesson.is_preview) && lesson.description && (
                          <p className="text-xs sm:text-sm text-gray-600 line-clamp-2 hidden sm:block">{lesson.description}</p>
                        )}
                      </div>

                      {/* Action Button */}
                      <div className="flex-shrink-0">
                        {(course.can_access || lesson.is_preview) ? (
                          <button
                            onClick={() => router.push(`/courses/${course.slug}/watch?lesson=${lesson.id}`)}
                            className="flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 bg-[#00B38F] hover:bg-[#00A87D] text-white rounded-lg transition-all"
                          >
                            <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                            </svg>
                          </button>
                        ) : (
                          <div className="flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 bg-gray-100 text-gray-400 rounded-lg border border-gray-200">
                            <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                            </svg>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-12">
                <svg className="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <p className="text-gray-500 font-medium">No lessons available yet</p>
              </div>
            )}
          </div>
        )}
      </div>
        </div>
      </div>
    </main>
  </div>
  );
}
