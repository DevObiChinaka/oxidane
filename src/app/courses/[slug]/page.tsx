'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';

interface Lesson {
  id: string;  // UUID
  title: string;
  description: string;
  video_source: 'upload' | 'youtube' | 'vimeo';
  video_url?: string;
  youtube_video_id?: string;
  duration: string;
  order: number;
  is_preview: boolean;
  is_completed?: boolean;
}

interface CourseDetail {
  id: string;  // UUID
  title: string;
  slug: string;
  short_description: string;
  description: string;
  thumbnail?: string;
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

  useEffect(() => {
    if (slug) {
      checkAuthAndFetchCourse();
    }
  }, [slug]);

  const checkAuthAndFetchCourse = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        // Not authenticated, redirect to login
        router.push('/auth');
        return;
      }

      // Verify token is valid
      const profileResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/profile/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!profileResponse.ok) {
        // Token invalid, clear storage and redirect
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        router.push('/auth');
        return;
      }

      setIsAuthenticated(true);
      await fetchCourseDetail();
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      router.push('/auth');
    }
  };

  const fetchCourseDetail = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`http://localhost:8000/api/courses/${slug}/`, {
        headers,
      });

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
      } else if (response.status === 401 || response.status === 403) {
        // Token expired or forbidden, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        router.push('/auth');
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
    const token = localStorage.getItem('access_token');
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
      const response = await fetch(`http://localhost:8000/api/courses/${slug}/enroll/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Enrollment response:', data);
        setSuccessMessage(data.message || 'Successfully enrolled in course!');
        setTimeout(() => setSuccessMessage(null), 1500);
        // Redirect to My Courses so user sees it added
        setTimeout(() => router.push('/my-courses'), 1600);
      } else if (response.status === 401 || response.status === 403) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        router.push('/auth');
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
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'intermediate':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'advanced':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#000856] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#00B38F]"></div>
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="min-h-screen bg-[#000856] flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-white mb-4">{error || 'Course not found'}</h2>
          <button
            onClick={() => router.push('/courses')}
            className="px-6 py-3 bg-[#00B38F] hover:bg-[#00A87D] text-white rounded-lg transition-all"
          >
            Back to Courses
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#000856] via-[#001347] to-[#000B2E]">
      {/* Success Toast Notification */}
      {successMessage && (
        <div className="fixed top-4 right-4 z-50 animate-slide-in-right">
          <div className="bg-gradient-to-r from-[#00D4A3] to-[#00B38F] text-white px-6 py-4 rounded-xl shadow-2xl flex items-center space-x-3 border border-[#00E5B5]">
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span className="font-semibold">{successMessage}</span>
          </div>
        </div>
      )}

      {/* Error Toast Notification */}
      {error && (
        <div className="fixed top-4 right-4 z-50 animate-slide-in-right">
          <div className="bg-red-500 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center space-x-3 border border-red-400">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="font-semibold">{error}</span>
            <button onClick={() => setError(null)} className="ml-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        <button
          onClick={() => router.push('/courses')}
          className="group flex items-center space-x-2 text-slate-400 hover:text-[#00B38F] transition-all"
        >
          <svg className="w-5 h-5 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          <span className="font-medium">Back to Courses</span>
        </button>
      </div>

      {/* Hero Section with Overlay Design */}
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content - Left Side */}
          <div className="lg:col-span-2">
            {/* Video/Thumbnail Card */}
            <div className="relative mb-6 group">
              {course.trailer_video_url ? (
                <div className="aspect-video bg-slate-900/50 backdrop-blur-sm rounded-2xl overflow-hidden border border-slate-700/50 shadow-2xl">
                  <iframe
                    src={course.trailer_video_url}
                    className="w-full h-full"
                    allowFullScreen
                  />
                </div>
              ) : (
                <div className="aspect-video bg-gradient-to-br from-[#00B38F]/10 via-[#001B7F]/20 to-[#000856]/30 rounded-2xl flex items-center justify-center border border-slate-700/50 shadow-2xl backdrop-blur-sm">
                  <div className="text-center">
                    <div className="w-32 h-32 mx-auto mb-4 bg-[#00B38F]/10 rounded-full flex items-center justify-center border-2 border-[#00B38F]/30">
                      <svg
                        className="w-16 h-16 text-[#00B38F]"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <p className="text-slate-400 text-lg">Course Preview</p>
                  </div>
                </div>
              )}
              
              {/* Floating badges on video */}
              <div className="absolute top-4 left-4 flex items-center space-x-2">
                <span className={`px-4 py-1.5 rounded-full text-sm font-semibold backdrop-blur-md ${
                  course.course_type === 'free' 
                    ? 'bg-green-500/90 text-white shadow-lg shadow-green-500/50' 
                    : 'bg-purple-500/90 text-white shadow-lg shadow-purple-500/50'
                }`}>
                  {course.course_type === 'free' ? '✓ Free Course' : '⭐ Premium'}
                </span>
              </div>

              <div className="absolute top-4 right-4">
                <span className={`px-4 py-1.5 rounded-full text-sm font-semibold backdrop-blur-md border-2 ${getDifficultyColor(course.difficulty_level)}`}>
                  {course.difficulty_level.charAt(0).toUpperCase() + course.difficulty_level.slice(1)}
                </span>
              </div>
            </div>

            {/* Course Title and Info */}
            <div className="bg-slate-900/30 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50 shadow-xl mb-6">
              <h1 className="text-4xl font-semibold text-white mb-4 leading-tight">{course.title}</h1>
              <p className="text-xl text-slate-300 mb-6 leading-relaxed">{course.short_description}</p>

              {/* Stats Row */}
              <div className="flex flex-wrap gap-6 mb-6">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-[#00B38F]/10 rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-[#00B38F]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm">Lessons</p>
                    <p className="text-white font-bold text-lg">{course.total_lessons}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm">Duration</p>
                    <p className="text-white font-bold text-lg">{course.estimated_duration}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-orange-500/10 rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm">Level</p>
                    <p className="text-white font-bold text-lg capitalize">{course.difficulty_level}</p>
                  </div>
                </div>
              </div>

              {/* Progress Bar (if enrolled) */}
              {course.is_enrolled && course.progress_percentage !== undefined && (
                <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700/30">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-white font-semibold">Your Progress</span>
                    <span className="text-2xl font-bold text-[#00B38F]">{course.progress_percentage}%</span>
                  </div>
                  <div className="h-3 bg-slate-700/50 rounded-full overflow-hidden mb-2">
                    <div
                      className="h-full bg-gradient-to-r from-[#00B38F] via-[#00D4A3] to-[#00E5B5] rounded-full transition-all duration-500 shadow-lg shadow-[#00B38F]/50"
                      style={{ width: `${course.progress_percentage}%` }}
                    />
                  </div>
                  <p className="text-sm text-slate-400">
                    {course.lessons_completed} of {course.total_lessons} lessons completed
                  </p>
                </div>
              )}
            </div>

            {/* About Course */}
            <div className="bg-slate-900/30 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50 shadow-xl mb-6">
              <h2 className="text-2xl font-semibold text-white mb-4 flex items-center">
                <svg className="w-7 h-7 mr-3 text-[#00D4A3]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                About This Course
              </h2>
              <div className="text-slate-300 text-lg leading-relaxed whitespace-pre-line">{course.description}</div>
            </div>

            {/* Lessons */}
            <div className="bg-slate-900/30 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50 shadow-xl">
              <h2 className="text-2xl font-semibold text-white mb-6 flex items-center">
                <svg className="w-7 h-7 mr-3 text-[#00D4A3]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                Course Content
              </h2>
              <div className="space-y-3">
                {course.lessons.length > 0 ? (
                  course.lessons.map((lesson, index) => (
                    <div
                      key={lesson.id}
                      className={`group relative overflow-hidden rounded-xl border transition-all duration-300 ${
                        lesson.is_completed
                          ? 'bg-[#00B38F]/5 border-[#00B38F]/40 hover:bg-[#00B38F]/10'
                          : 'bg-slate-800/30 border-slate-700/50 hover:bg-slate-800/50 hover:border-slate-600'
                      }`}
                    >
                      <div className="p-5">
                        <div className="flex items-start justify-between">
                          <div className="flex-1 mr-4">
                            {/* Lesson Header */}
                            <div className="flex items-center space-x-3 mb-3">
                              <span className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-[#00D4A3]/20 to-[#00B38F]/20 text-[#00D4A3] font-semibold border border-[#00D4A3]/30">
                                {lesson.order}
                              </span>
                              
                              {lesson.is_preview && (
                                <span className="px-3 py-1 bg-[#00D4A3]/10 text-[#00D4A3] text-xs font-medium rounded-full border border-[#00D4A3]/30">
                                  🎁 Free Preview
                                </span>
                              )}
                              
                              {lesson.is_completed && (
                                <div className="flex items-center space-x-1 px-3 py-1 bg-[#00D4A3]/10 text-[#00D4A3] text-xs font-medium rounded-full border border-[#00D4A3]/30">
                                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                  </svg>
                                  <span>Completed</span>
                                </div>
                              )}

                              <span className="flex items-center space-x-1 text-slate-400 text-sm">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <span>{lesson.duration}</span>
                              </span>
                            </div>
                            
                            {/* Lesson Title */}
                            <h3 className="text-white font-medium text-lg mb-2 group-hover:text-[#00D4A3] transition-colors">
                              {lesson.title}
                            </h3>
                            
                            {/* Lesson Description */}
                            {(course.can_access || lesson.is_preview) && (
                              <p className="text-slate-400 text-sm leading-relaxed">{lesson.description}</p>
                            )}
                          </div>
                          
                          {/* Action Button */}
                          <div className="flex items-center space-x-2">
                            {(course.can_access || lesson.is_preview) ? (
                              <button
                                onClick={() => router.push(`/courses/${course.slug}/watch?lesson=${lesson.id}`)}
                                className="group/btn flex items-center justify-center w-12 h-12 bg-gradient-to-br from-[#00D4A3] to-[#00B38F] hover:from-[#00E5B5] hover:to-[#00C99F] text-white rounded-xl transition-all shadow-lg hover:shadow-[#00D4A3]/50 hover:scale-110"
                              >
                                <svg className="w-5 h-5 group-hover/btn:scale-110 transition-transform" fill="currentColor" viewBox="0 0 20 20">
                                  <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                                </svg>
                              </button>
                            ) : (
                              <div className="flex items-center justify-center w-12 h-12 bg-slate-700/30 text-slate-600 rounded-xl border border-slate-600/30">
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                </svg>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      {/* Progress Bar for Lesson */}
                      {lesson.is_completed && (
                        <div className="h-1 bg-gradient-to-r from-[#00D4A3] to-[#00B38F]"></div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-center py-12">
                    <div className="w-20 h-20 mx-auto mb-4 bg-slate-800/50 rounded-full flex items-center justify-center">
                      <svg className="w-10 h-10 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                    </div>
                    <p className="text-slate-400 text-lg">No lessons available yet</p>
                    <p className="text-slate-500 text-sm mt-2">Check back soon for new content</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Sidebar - Right Side */}
          <div className="lg:col-span-1 space-y-6">
            {/* CTA Card */}
            <div className="bg-gradient-to-br from-slate-900/50 to-slate-800/30 backdrop-blur-sm rounded-2xl p-6 border border-slate-700/50 shadow-xl">
              {course.can_access ? (
                <>
                  <button
                    onClick={handleStartLearning}
                    className="w-full px-6 py-4 bg-gradient-to-r from-[#00D4A3] to-[#00B38F] hover:from-[#00E5B5] hover:to-[#00C99F] text-white rounded-xl transition-all font-semibold text-lg shadow-lg hover:shadow-[#00D4A3]/50 hover:scale-[1.02] transform flex items-center justify-center space-x-2 mb-4"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>{course.is_enrolled ? 'Continue Learning' : 'Start Learning'}</span>
                  </button>
                  <p className="text-center text-sm text-slate-400">
                    {course.is_enrolled ? 'Resume where you left off' : 'Begin your learning journey'}
                  </p>
                </>
              ) : course.requires_subscription ? (
                <>
                  <div className="text-center mb-4">
                    <div className="w-16 h-16 mx-auto mb-3 bg-purple-500/10 rounded-full flex items-center justify-center">
                      <svg className="w-8 h-8 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                    </div>
                    <h3 className="text-white font-semibold text-lg mb-2">Premium Content</h3>
                    <p className="text-slate-400 text-sm mb-4">
                      This course requires an active mentorship subscription
                    </p>
                  </div>
                  <button
                    onClick={() => router.push('/pricing')}
                    className="w-full px-6 py-4 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600 text-white rounded-xl transition-all font-semibold text-lg shadow-lg hover:shadow-purple-500/50 hover:scale-[1.02] transform flex items-center justify-center space-x-2"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                    </svg>
                    <span>Get Mentorship Access</span>
                  </button>
                </>
              ) : (
                <>
                  <div className="text-center mb-4">
                    <div className="w-16 h-16 mx-auto mb-3 bg-[#00D4A3]/10 rounded-full flex items-center justify-center">
                      <svg className="w-8 h-8 text-[#00D4A3]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <h3 className="text-white font-semibold text-lg mb-2">Free Course</h3>
                    <p className="text-slate-400 text-sm mb-4">
                      Enroll now and start learning for free
                    </p>
                  </div>
                  <button
                    onClick={handleEnroll}
                    disabled={enrolling}
                    className="w-full px-6 py-4 bg-gradient-to-r from-[#00D4A3] to-[#00B38F] hover:from-[#00E5B5] hover:to-[#00C99F] text-white rounded-xl transition-all font-semibold text-lg shadow-lg hover:shadow-[#00D4A3]/50 hover:scale-[1.02] transform disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center space-x-2"
                  >
                    {enrolling ? (
                      <>
                        <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-white"></div>
                        <span>Enrolling...</span>
                      </>
                    ) : (
                      <>
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                        <span>Enroll Now</span>
                      </>
                    )}
                  </button>
                </>
              )}
            </div>

            {/* Course Stats Card */}
            <div className="bg-slate-900/30 backdrop-blur-sm rounded-2xl p-6 border border-slate-700/50 shadow-xl">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <svg className="w-6 h-6 mr-2 text-[#00D4A3]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                Course Stats
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-slate-800/30 rounded-xl">
                  <span className="text-slate-400 flex items-center">
                    <svg className="w-5 h-5 mr-2 text-[#00D4A3]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                    Total Lessons
                  </span>
                  <span className="text-white font-semibold text-lg">{course.total_lessons}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-slate-800/30 rounded-xl">
                  <span className="text-slate-400 flex items-center">
                    <svg className="w-5 h-5 mr-2 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Duration
                  </span>
                  <span className="text-white font-semibold text-lg">{course.estimated_duration}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-slate-800/30 rounded-xl">
                  <span className="text-slate-400 flex items-center">
                    <svg className="w-5 h-5 mr-2 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    Difficulty
                  </span>
                  <span className="text-white font-semibold text-lg capitalize">{course.difficulty_level}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-slate-800/30 rounded-xl">
                  <span className="text-slate-400 flex items-center">
                    <svg className="w-5 h-5 mr-2 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                    </svg>
                    Type
                  </span>
                  <span className="text-white font-semibold text-lg capitalize">{course.course_type}</span>
                </div>
              </div>
            </div>

            {/* Quick Actions Card */}
            <div className="bg-slate-900/30 backdrop-blur-sm rounded-2xl p-6 border border-slate-700/50 shadow-xl">
              <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <button
                  onClick={() => router.push('/courses')}
                  className="w-full px-4 py-3 bg-slate-800/50 hover:bg-slate-700/70 text-white rounded-xl transition-all flex items-center justify-center space-x-2 group"
                >
                  <svg className="w-5 h-5 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  <span>Browse More Courses</span>
                </button>
                {course.is_enrolled && (
                  <button
                    onClick={() => router.push('/my-courses')}
                    className="w-full px-4 py-3 bg-slate-800/50 hover:bg-slate-700/70 text-white rounded-xl transition-all flex items-center justify-center space-x-2 group"
                  >
                    <svg className="w-5 h-5 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span>My Courses</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
