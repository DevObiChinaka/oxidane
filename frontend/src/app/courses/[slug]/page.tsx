'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';

interface Lesson {
  id: string;
  title: string;
  description: string;
  video_source: 'upload' | 'youtube' | 'vimeo';
  video_url?: string;
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
  const [showVideo, setShowVideo] = useState(false);
  const [videoTimeElapsed, setVideoTimeElapsed] = useState(0);
  const playerRef = useRef<any>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (slug) {
      checkAuthAndFetchCourse();
    }
  }, [slug]);

  useEffect(() => {
    // Cleanup timeout on unmount
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // YouTube API player control
  useEffect(() => {
    if (showVideo && videoTimeElapsed === 0) {
      // Load YouTube IFrame API
      const tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      const firstScriptTag = document.getElementsByTagName('script')[0];
      firstScriptTag.parentNode?.insertBefore(tag, firstScriptTag);

      // Set up YouTube player
      (window as any).onYouTubeIframeAPIReady = () => {
        const previewLesson = getFirstPreviewLesson();
        if (previewLesson?.video_source === 'youtube' && previewLesson.youtube_video_id) {
          playerRef.current = new (window as any).YT.Player('youtube-player', {
            events: {
              onReady: (event: any) => {
                event.target.playVideo();
                // Stop after 10 seconds
                timeoutRef.current = setTimeout(() => {
                  event.target.pauseVideo();
                  setVideoTimeElapsed(10);
                }, 10000);
              },
            },
          });
        }
      };
    }
  }, [showVideo]);

  const checkAuthAndFetchCourse = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        // Not authenticated, redirect to login
        router.push('/auth');
        return;
      }

      // Verify token is valid
      const profileResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/auth/profile/`, {
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
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'intermediate':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'advanced':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  const getDifficultyIcon = (level: string) => {
    switch (level) {
      case 'beginner':
        return '🌱';
      case 'intermediate':
        return '⚡';
      case 'advanced':
        return '🚀';
      default:
        return '📚';
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

  const getFirstPreviewLesson = () => {
    return course?.lessons.find(lesson => lesson.is_preview) || course?.lessons[0];
  };

  const handlePlayPreview = () => {
    setShowVideo(true);
    setVideoTimeElapsed(0);
  };

  const handleReplayPreview = () => {
    setVideoTimeElapsed(0);
    setShowVideo(false);
    setTimeout(() => setShowVideo(true), 100);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#00B38F]"></div>
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
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
    );
  }

  const previewLesson = getFirstPreviewLesson();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50">
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

      {/* Navigation Header */}
      <div className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <button
            onClick={() => router.push('/courses')}
            className="group inline-flex items-center space-x-2 text-gray-600 hover:text-[#00B38F] transition-colors"
          >
            <svg className="w-5 h-5 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span className="font-medium">Back to Courses</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column - Main Content */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Video Preview Section */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="relative aspect-video bg-gradient-to-br from-gray-900 to-gray-800">
                {showVideo && previewLesson ? (
                  <iframe
                    id="youtube-player"
                    src={getVideoEmbedUrl(previewLesson)}
                    className="absolute inset-0 w-full h-full"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                ) : (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-[#000856] via-[#001B4D] to-[#000856] text-white">
                    {videoTimeElapsed > 0 ? (
                      <div className="text-center space-y-4">
                        <div className="w-20 h-20 mx-auto bg-white/10 backdrop-blur-sm rounded-full flex items-center justify-center border border-white/20">
                          <svg className="w-10 h-10 text-[#00B38F]" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                          </svg>
                        </div>
                        <div>
                          <p className="text-lg font-semibold mb-2">Preview Ended</p>
                          <p className="text-sm text-gray-300 mb-4">Want to see more?</p>
                          <button
                            onClick={handleReplayPreview}
                            className="px-6 py-2.5 bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 rounded-lg transition-all"
                          >
                            Replay Preview
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center space-y-4">
                        <div className="w-20 h-20 mx-auto bg-white/10 backdrop-blur-sm rounded-full flex items-center justify-center border border-white/20">
                          <svg className="w-10 h-10 text-[#00B38F]" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                          </svg>
                        </div>
                        <div>
                          <p className="text-lg font-semibold mb-2">Course Preview Available</p>
                          <p className="text-sm text-gray-300 mb-4">Watch a 10-second preview</p>
                          <button
                            onClick={handlePlayPreview}
                            className="px-6 py-2.5 bg-gradient-to-r from-[#00B38F] to-[#00A87D] hover:from-[#00C99F] hover:to-[#00B38F] rounded-lg transition-all shadow-lg hover:shadow-xl"
                          >
                            Play Preview
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                {/* Floating Badges */}
                <div className="absolute top-4 left-4 flex items-center space-x-2">
                  <span className={`px-3 py-1.5 rounded-full text-xs font-semibold backdrop-blur-md border ${
                    course.course_type === 'free' 
                      ? 'bg-emerald-500/90 text-white border-emerald-400/50' 
                      : 'bg-purple-500/90 text-white border-purple-400/50'
                  }`}>
                    {course.course_type === 'free' ? '✓ Free' : '⭐ Premium'}
                  </span>
                </div>
              </div>
            </div>

            {/* Course Header */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h1 className="text-3xl font-bold text-gray-900 mb-3 leading-tight">{course.title}</h1>
                  <p className="text-lg text-gray-600 leading-relaxed">{course.short_description}</p>
                </div>
                <span className={`ml-4 px-4 py-2 rounded-full text-sm font-semibold border ${getDifficultyColor(course.difficulty_level)}`}>
                  {getDifficultyIcon(course.difficulty_level)} {course.difficulty_level.charAt(0).toUpperCase() + course.difficulty_level.slice(1)}
                </span>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-200">
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-[#00B38F]/10 to-[#00A87D]/10 rounded-xl mb-2">
                    <svg className="w-6 h-6 text-[#00B38F]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                  </div>
                  <p className="text-2xl font-bold text-gray-900">{course.total_lessons}</p>
                  <p className="text-sm text-gray-500">Lessons</p>
                </div>
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-blue-500/10 to-blue-600/10 rounded-xl mb-2">
                    <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <p className="text-2xl font-bold text-gray-900">{course.estimated_duration}</p>
                  <p className="text-sm text-gray-500">Duration</p>
                </div>
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-purple-500/10 to-purple-600/10 rounded-xl mb-2">
                    <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                  </div>
                  <p className="text-2xl font-bold text-gray-900">{course.is_enrolled ? 'Enrolled' : 'Open'}</p>
                  <p className="text-sm text-gray-500">Status</p>
                </div>
              </div>

              {/* Progress Bar (if enrolled) */}
              {course.is_enrolled && course.progress_percentage !== undefined && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-semibold text-gray-700">Your Progress</span>
                    <span className="text-2xl font-bold bg-gradient-to-r from-[#00B38F] to-[#00A87D] bg-clip-text text-transparent">
                      {course.progress_percentage}%
                    </span>
                  </div>
                  <div className="h-2.5 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-[#00B38F] to-[#00C99F] rounded-full transition-all duration-500"
                      style={{ width: `${course.progress_percentage}%` }}
                    />
                  </div>
                  <p className="text-sm text-gray-500 mt-2">
                    {course.lessons_completed} of {course.total_lessons} lessons completed
                  </p>
                </div>
              )}
            </div>

            {/* About Course */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
              <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                <div className="w-8 h-8 bg-gradient-to-br from-[#00B38F]/10 to-[#00A87D]/10 rounded-lg flex items-center justify-center mr-3">
                  <svg className="w-5 h-5 text-[#00B38F]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                About This Course
              </h2>
              <div className="prose prose-gray max-w-none">
                <p className="text-gray-600 leading-relaxed whitespace-pre-line">{course.description}</p>
              </div>
            </div>

            {/* Course Content */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
              <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
                <div className="w-8 h-8 bg-gradient-to-br from-[#00B38F]/10 to-[#00A87D]/10 rounded-lg flex items-center justify-center mr-3">
                  <svg className="w-5 h-5 text-[#00B38F]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                </div>
                Course Curriculum
              </h2>
              
              <div className="space-y-3">
                {course.lessons.length > 0 ? (
                  course.lessons.map((lesson) => (
                    <div
                      key={lesson.id}
                      className={`group relative rounded-xl border transition-all duration-200 ${
                        lesson.is_completed
                          ? 'bg-emerald-50/50 border-emerald-200 hover:border-emerald-300'
                          : 'bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm'
                      }`}
                    >
                      <div className="p-5">
                        <div className="flex items-start justify-between">
                          <div className="flex-1 mr-4">
                            {/* Lesson Header */}
                            <div className="flex items-center space-x-3 mb-2">
                              <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-gray-100 to-gray-50 text-gray-700 text-sm font-semibold border border-gray-200">
                                {lesson.order}
                              </span>
                              
                              {lesson.is_preview && (
                                <span className="px-2.5 py-1 bg-emerald-100 text-emerald-700 text-xs font-medium rounded-md">
                                  Free
                                </span>
                              )}
                              
                              {lesson.is_completed && (
                                <div className="flex items-center space-x-1 px-2.5 py-1 bg-emerald-100 text-emerald-700 text-xs font-medium rounded-md">
                                  <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                  </svg>
                                  <span>Done</span>
                                </div>
                              )}

                              <span className="flex items-center space-x-1 text-gray-500 text-xs">
                                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <span>{lesson.duration}</span>
                              </span>
                            </div>
                            
                            {/* Lesson Title */}
                            <h3 className="text-gray-900 font-semibold text-base mb-1 group-hover:text-[#00B38F] transition-colors">
                              {lesson.title}
                            </h3>
                            
                            {/* Lesson Description */}
                            {(course.can_access || lesson.is_preview) && (
                              <p className="text-gray-600 text-sm leading-relaxed">{lesson.description}</p>
                            )}
                          </div>
                          
                          {/* Action Button */}
                          <div className="flex-shrink-0">
                            {(course.can_access || lesson.is_preview) ? (
                              <button
                                onClick={() => router.push(`/courses/${course.slug}/watch?lesson=${lesson.id}`)}
                                className="group/btn flex items-center justify-center w-11 h-11 bg-gradient-to-br from-[#00B38F] to-[#00A87D] hover:from-[#00C99F] hover:to-[#00B38F] text-white rounded-xl transition-all shadow-md hover:shadow-lg"
                              >
                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                  <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                                </svg>
                              </button>
                            ) : (
                              <div className="flex items-center justify-center w-11 h-11 bg-gray-100 text-gray-400 rounded-xl border border-gray-200">
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                  <div className="text-center py-16">
                    <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                      <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                    </div>
                    <p className="text-gray-500 font-medium">No lessons available yet</p>
                    <p className="text-gray-400 text-sm mt-1">Check back soon for new content</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Sidebar */}
          <div className="lg:col-span-1">
            <div className="sticky top-24 space-y-6">
              
              {/* CTA Card */}
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                {course.can_access ? (
                  <div className="space-y-4">
                    <button
                      onClick={handleStartLearning}
                      className="w-full px-6 py-4 bg-gradient-to-r from-[#00B38F] to-[#00A87D] hover:from-[#00C99F] hover:to-[#00B38F] text-white rounded-xl transition-all font-semibold shadow-lg hover:shadow-xl flex items-center justify-center space-x-2"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>{course.is_enrolled ? 'Continue Learning' : 'Start Learning'}</span>
                    </button>
                    <p className="text-center text-sm text-gray-500">
                      {course.is_enrolled ? 'Pick up where you left off' : 'Begin your journey today'}
                    </p>
                  </div>
                ) : course.requires_subscription ? (
                  <div className="space-y-4">
                    <div className="text-center mb-4">
                      <div className="w-14 h-14 mx-auto mb-3 bg-gradient-to-br from-purple-100 to-purple-50 rounded-2xl flex items-center justify-center">
                        <svg className="w-7 h-7 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                        </svg>
                      </div>
                      <h3 className="font-bold text-gray-900 mb-1">Premium Course</h3>
                      <p className="text-sm text-gray-600">
                        Requires active mentorship subscription
                      </p>
                    </div>
                    <button
                      onClick={() => router.push('/pricing')}
                      className="w-full px-6 py-4 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600 text-white rounded-xl transition-all font-semibold shadow-lg hover:shadow-xl flex items-center justify-center space-x-2"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                      </svg>
                      <span>Upgrade to Premium</span>
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="text-center mb-4">
                      <div className="w-14 h-14 mx-auto mb-3 bg-gradient-to-br from-emerald-100 to-emerald-50 rounded-2xl flex items-center justify-center">
                        <svg className="w-7 h-7 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                        </svg>
                      </div>
                      <h3 className="font-bold text-gray-900 mb-1">Free Course</h3>
                      <p className="text-sm text-gray-600">
                        Start learning at no cost
                      </p>
                    </div>
                    <button
                      onClick={handleEnroll}
                      disabled={enrolling}
                      className="w-full px-6 py-4 bg-gradient-to-r from-[#00B38F] to-[#00A87D] hover:from-[#00C99F] hover:to-[#00B38F] text-white rounded-xl transition-all font-semibold shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                    >
                      {enrolling ? (
                        <>
                          <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                          <span>Enrolling...</span>
                        </>
                      ) : (
                        <>
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                          </svg>
                          <span>Enroll for Free</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>

              {/* Course Details Card */}
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                <h3 className="font-bold text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-[#00B38F]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Course Details
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between py-2 border-b border-gray-100">
                    <span className="text-sm text-gray-600">Lessons</span>
                    <span className="font-semibold text-gray-900">{course.total_lessons}</span>
                  </div>
                  <div className="flex items-center justify-between py-2 border-b border-gray-100">
                    <span className="text-sm text-gray-600">Duration</span>
                    <span className="font-semibold text-gray-900">{course.estimated_duration}</span>
                  </div>
                  <div className="flex items-center justify-between py-2 border-b border-gray-100">
                    <span className="text-sm text-gray-600">Level</span>
                    <span className="font-semibold text-gray-900 capitalize">{course.difficulty_level}</span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-sm text-gray-600">Access</span>
                    <span className="font-semibold text-gray-900 capitalize">{course.course_type}</span>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                <h3 className="font-bold text-gray-900 mb-4">Quick Actions</h3>
                <div className="space-y-2">
                  <button
                    onClick={() => router.push('/courses')}
                    className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded-lg transition-all flex items-center justify-center space-x-2 font-medium"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                    <span>Browse Courses</span>
                  </button>
                  {course.is_enrolled && (
                    <button
                      onClick={() => router.push('/my-courses')}
                      className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded-lg transition-all flex items-center justify-center space-x-2 font-medium"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
    </div>
  );
}
