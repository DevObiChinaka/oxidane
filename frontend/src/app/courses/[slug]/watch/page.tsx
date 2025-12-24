'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams, useSearchParams } from 'next/navigation';
import { CheckCircleIcon, XMarkIcon, TrophyIcon } from '@heroicons/react/24/solid';
import { apiGet, apiPost } from '@/lib/api';
import SecureVideoPlayer from '@/components/user/SecureVideoPlayer';

interface Lesson {
  id: string;  // UUID
  title: string;
  description: string;
  video_source: 'upload' | 'youtube' | 'vimeo';
  video_url?: string;
  video_file_url?: string;  // For uploaded videos
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
  course_type: 'free' | 'premium';
  can_access: boolean;
  is_enrolled: boolean;
  progress_percentage?: number;
  lessons_completed?: number;
  total_lessons: number;
  lessons: Lesson[];
}

export default function VideoPlayerPage() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const slug = params?.slug as string;
  const lessonIdParam = searchParams?.get('lesson');

  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [currentLesson, setCurrentLesson] = useState<Lesson | null>(null);
  const [loading, setLoading] = useState(true);
  const [marking, setMarking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showCompletionModal, setShowCompletionModal] = useState(false);
  const [showAutoAdvanceNotification, setShowAutoAdvanceNotification] = useState(false);
  const [autoAdvanceCountdown, setAutoAdvanceCountdown] = useState(5);
  const [showCompletedToast, setShowCompletedToast] = useState(false);
  const [videoKey, setVideoKey] = useState(0);
  // Cache for pre-loaded video embeds
  const [videoEmbedCache, setVideoEmbedCache] = useState<Map<string, string>>(new Map());
  const [preloadingVideos, setPreloadingVideos] = useState(false);

  useEffect(() => {
    if (slug) {
      checkAuthAndFetchCourse();
    }
  }, [slug]);

  // Update lesson immediately when lessonIdParam changes
  useEffect(() => {
    if (course && course.lessons.length > 0 && lessonIdParam) {
      const lesson = course.lessons.find(l => l.id === lessonIdParam);
      if (lesson && lesson.id !== currentLesson?.id) {
        setCurrentLesson(lesson);
        // Force video player to remount
        setVideoKey(prev => prev + 1);
      }
    }
  }, [lessonIdParam, course]);

  // Pre-load all video embeds when course loads
  useEffect(() => {
    if (course && course.lessons.length > 0 && videoEmbedCache.size === 0) {
      preloadAllVideoEmbeds();
    }
  }, [course]);

  // Set initial lesson when course loads
  useEffect(() => {
    if (course && course.lessons.length > 0 && !currentLesson) {
      if (lessonIdParam) {
        const lesson = course.lessons.find(l => l.id === lessonIdParam);
        if (lesson) {
          setCurrentLesson(lesson);
          setVideoKey(prev => prev + 1);
        } else {
          setCurrentLesson(course.lessons[0]);
          setVideoKey(prev => prev + 1);
        }
      } else {
        // Find first incomplete lesson or first lesson
        const firstIncomplete = course.lessons.find(l => !l.is_completed);
        setCurrentLesson(firstIncomplete || course.lessons[0]);
        setVideoKey(prev => prev + 1);
      }
    }
  }, [course]);

  const preloadAllVideoEmbeds = async () => {
    if (!course || preloadingVideos) return;

    setPreloadingVideos(true);

    try {
      const token = localStorage.getItem('user_auth_token') || localStorage.getItem('access_token');
      if (!token) return;

      const cache = new Map<string, string>();
      
      // Fetch all video embeds in parallel
      const promises = course.lessons.map(async (lesson) => {
        try {
          const timestamp = new Date().getTime();
          const response = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/lessons/${lesson.id}/video-embed/?t=${timestamp}`,
            {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              },
              cache: 'no-store'
            }
          );

          if (response.ok) {
            const data = await response.json();
            cache.set(lesson.id, data.embed_html);
          }
        } catch (error) {
          // Silent fail for individual videos
        }
      });

      await Promise.all(promises);
      
      setVideoEmbedCache(cache);
    } catch (error) {
      // Silent fail
    } finally {
      setPreloadingVideos(false);
    }
  };

  const checkAuthAndFetchCourse = async () => {
    try {
      // Verify token is valid
      const profileResponse = await apiGet('/auth/profile/');

      if (!profileResponse.ok) {
        return;
      }

      setIsAuthenticated(true);
      await fetchCourseAndLessons();
    } catch (error) {
      // Silent fail
    }
  };

  const fetchCourseAndLessons = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiGet(`/courses/${slug}/`);

      if (response.ok) {
        const data = await response.json();
        
        // Check access
        if (!data.can_access && !(currentLesson?.is_preview)) {
          setError('You do not have access to this course');
          return;
        }

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
        setError('Failed to load course');
      }
    } catch (err) {
      setError('Failed to load course');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkComplete = async () => {
    if (!currentLesson || !course) return;

    const token = localStorage.getItem('user_auth_token') || localStorage.getItem('access_token');
    if (!token) {
      router.push('/auth');
      return;
    }

    try {
      setMarking(true);
      const response = await apiPost(
        `/courses/lessons/${currentLesson.id}/progress/`,
        {
          is_completed: true,
          time_spent: 0, // You could track actual time spent
        }
      );

      if (response.ok) {
        const data = await response.json();

        // Update the course state with the new progress data and mark lesson as complete
        const updatedLessons = course.lessons.map(l =>
          l.id === currentLesson.id ? { ...l, is_completed: true } : l
        );
        
        const updatedCourse = {
          ...course,
          lessons: updatedLessons,
          progress_percentage: data.course_progress?.completion_percentage || course.progress_percentage,
          lessons_completed: data.course_progress?.lessons_completed || course.lessons_completed,
        };
        
        setCourse(updatedCourse);
        
        // Show completed toast
        setShowCompletedToast(true);
        setTimeout(() => setShowCompletedToast(false), 3000);
        
        // Find the next lesson after the current one
        const currentIndex = updatedCourse.lessons.findIndex(l => l.id === currentLesson.id);
        if (currentIndex < updatedCourse.lessons.length - 1) {
          const nextLesson = updatedCourse.lessons[currentIndex + 1];
          // Navigate to next lesson - this will trigger the useEffect to update currentLesson
          router.push(`/courses/${slug}/watch?lesson=${nextLesson.id}`);
        } else {
          // Course completed - show modal
          setShowCompletionModal(true);
        }
      } else {
        const errorData = await response.json().catch(() => ({}));
        alert('Failed to mark lesson as complete. Please try again.');
      }
    } catch (err) {
      // Silent fail
    } finally {
      setMarking(false);
    }
  };

  const selectLesson = (lesson: Lesson) => {
    // Update state immediately AND change URL
    setCurrentLesson(lesson);
    setVideoKey(prev => prev + 1);
    router.push(`/courses/${slug}/watch?lesson=${lesson.id}`, { scroll: false });
  };

  const handleVideoEnd = () => {
    // Automatically mark as complete and advance when video ends
    if (currentLesson && !currentLesson.is_completed) {
      // Mark as complete first, then show notification
      handleMarkComplete();
    } else if (currentLesson && currentLesson.is_completed) {
      // Already completed, show notification before advancing
      setShowAutoAdvanceNotification(true);
      setAutoAdvanceCountdown(5);
      
      // Start countdown
      const countdownInterval = setInterval(() => {
        setAutoAdvanceCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(countdownInterval);
            setShowAutoAdvanceNotification(false);
            autoAdvanceToNextLesson();
            return 5;
          }
          return prev - 1;
        });
      }, 1000);
    }
  };

  const autoAdvanceToNextLesson = () => {
    if (!course || !currentLesson) return;
    
    const currentIndex = course.lessons.findIndex(l => l.id === currentLesson.id);
    if (currentIndex < course.lessons.length - 1) {
      const nextLesson = course.lessons[currentIndex + 1];
      router.push(`/courses/${slug}/watch?lesson=${nextLesson.id}`);
    } else {
      // Course completed - show modal
      setShowCompletionModal(true);
    }
  };

  const getVideoPlayer = () => {
    if (!currentLesson) return null;

    // Get cached embed HTML for current lesson
    const cachedEmbed = videoEmbedCache.get(currentLesson.id);

    // Use SecureVideoPlayer with cached embed
    return (
      <SecureVideoPlayer
        key={`${currentLesson.id}-${videoKey}`}
        lessonId={currentLesson.id}
        lessonTitle={currentLesson.title}
        videoSource={currentLesson.video_source}
        onVideoEnd={handleVideoEnd}
        className="w-full h-full"
        preloadedEmbed={cachedEmbed}
        isPreloading={preloadingVideos}
      />
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-gray-200 border-t-[#00B38F] mx-auto mb-4"></div>
          <p className="text-gray-600">Loading course...</p>
        </div>
      </div>
    );
  }

  if (error || !course || !currentLesson) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-rose-100 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">{error || 'Content not available'}</h2>
          <p className="text-gray-600 mb-6">We couldn't load this content</p>
          <button
            onClick={() => router.push('/courses')}
            className="px-6 py-3 bg-gradient-to-r from-[#00B38F] to-[#00A87D] hover:from-[#00C99F] hover:to-[#00B38F] text-white rounded-lg transition-all shadow-lg"
          >
            Back to Courses
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex flex-col lg:flex-row">
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col">
          
          {/* Video Player Container */}
          <div className="bg-gray-50 px-2 py-3 sm:px-4 sm:py-4 lg:px-8 lg:py-8">
            <div className="max-w-7xl mx-auto">
              <div className="aspect-video w-full bg-black rounded-lg sm:rounded-xl overflow-hidden shadow-lg sm:shadow-2xl">
                {getVideoPlayer()}
              </div>
            </div>
            
            {/* Auto-Advance Notification */}
            {showAutoAdvanceNotification && (
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/60 to-transparent p-6">
                <div className="max-w-2xl mx-auto bg-white/95 backdrop-blur-md rounded-xl p-5 shadow-2xl border border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="relative flex-shrink-0">
                        <svg className="w-12 h-12 transform -rotate-90">
                          <circle
                            cx="24"
                            cy="24"
                            r="20"
                            stroke="#E5E7EB"
                            strokeWidth="4"
                            fill="none"
                          />
                          <circle
                            cx="24"
                            cy="24"
                            r="20"
                            stroke="#10b981"
                            strokeWidth="4"
                            fill="none"
                            strokeDasharray={`${2 * Math.PI * 20}`}
                            strokeDashoffset={`${2 * Math.PI * 20 * (1 - autoAdvanceCountdown / 5)}`}
                            className="transition-all duration-1000 ease-linear"
                          />
                        </svg>
                        <span className="absolute inset-0 flex items-center justify-center text-gray-900 text-base font-bold">
                          {autoAdvanceCountdown}
                        </span>
                      </div>
                      <div>
                        <p className="text-gray-900 font-semibold text-base">Next lesson starting soon</p>
                        <p className="text-gray-600 text-sm">Automatically advancing in {autoAdvanceCountdown} seconds</p>
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        setShowAutoAdvanceNotification(false);
                        setAutoAdvanceCountdown(5);
                      }}
                      className="px-5 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-900 rounded-lg transition-all text-sm font-medium shadow-sm"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Content Section */}
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-5xl mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8">
              
              {/* Breadcrumb Navigation */}
              <nav className="flex items-center space-x-1 sm:space-x-2 text-xs sm:text-sm text-gray-600 mb-3 sm:mb-4 lg:mb-6 overflow-x-auto pb-1">
                <button
                  onClick={() => router.push('/courses')}
                  className="hover:text-[#00B38F] transition-colors font-medium whitespace-nowrap flex-shrink-0"
                >
                  Courses
                </button>
                <svg className="w-3 h-3 sm:w-4 sm:h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
                <button
                  onClick={() => router.push(`/courses/${course.slug}`)}
                  className="hover:text-[#00B38F] transition-colors font-medium truncate max-w-[120px] sm:max-w-xs"
                  title={course.title}
                >
                  {course.title}
                </button>
                <svg className="w-3 h-3 sm:w-4 sm:h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
                <span className="text-gray-900 font-medium whitespace-nowrap flex-shrink-0">Lesson {currentLesson.order}</span>
              </nav>

              {/* Lesson Header */}
              <div className="mb-4 sm:mb-6 lg:mb-8">
                <div className="flex flex-col sm:flex-row items-start justify-between gap-2 sm:gap-4 mb-4 sm:mb-6">
                  <h1 className="text-xl sm:text-2xl lg:text-4xl font-bold text-gray-900 leading-tight flex-1">
                    {currentLesson.title}
                  </h1>
                  <span className="px-3 py-1.5 sm:px-4 sm:py-2 bg-gray-100 text-gray-700 text-xs sm:text-sm font-semibold rounded-lg whitespace-nowrap">
                    {currentLesson.duration}
                  </span>
                </div>

                {/* Action Button */}
                <div className="flex items-center space-x-3 sm:space-x-4">
                  {!currentLesson.is_completed ? (
                    <button
                      onClick={handleMarkComplete}
                      disabled={marking}
                      className="px-4 py-2.5 sm:px-6 sm:py-3 lg:px-8 lg:py-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 sm:space-x-3 font-semibold text-sm sm:text-base"
                    >
                      {marking ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-2 border-white border-t-transparent"></div>
                          <span className="hidden sm:inline">Marking Complete...</span>
                          <span className="sm:hidden">Marking...</span>
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                          </svg>
                          <span className="hidden sm:inline">Mark as Complete</span>
                          <span className="sm:hidden">Complete</span>
                        </>
                      )}
                    </button>
                  ) : (
                    <div className="inline-flex items-center justify-center space-x-2 sm:space-x-3 px-4 py-2.5 sm:px-6 sm:py-3 lg:px-8 lg:py-4 bg-emerald-50 border-2 border-emerald-500 text-emerald-700 rounded-lg shadow-sm">
                      <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span className="font-semibold text-sm sm:text-base">Completed</span>
                    </div>
                  )}
                </div>
              </div>

              {/* About This Lesson */}
              <div className="bg-white rounded-lg sm:rounded-xl shadow-sm border border-gray-200 p-4 sm:p-6 lg:p-8">
                <h2 className="text-base sm:text-lg lg:text-xl font-bold text-gray-900 mb-3 sm:mb-4 flex items-center">
                  <div className="w-7 h-7 sm:w-8 sm:h-8 bg-emerald-100 rounded-lg flex items-center justify-center mr-2 sm:mr-3">
                    <svg className="w-4 h-4 sm:w-5 sm:h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  About This Lesson
                </h2>
                <p className="text-sm sm:text-base text-gray-600 leading-relaxed whitespace-pre-line">{currentLesson.description}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar - Course Progress & Lessons */}
        <div className="lg:w-[420px] bg-white border-t lg:border-t-0 lg:border-l border-gray-200 overflow-y-auto flex-shrink-0">
          <div className="sticky top-0 bg-white border-b border-gray-200 p-4 sm:p-5 lg:p-6 z-10">
            <h2 className="text-lg sm:text-xl font-bold text-gray-900 mb-4 sm:mb-5 lg:mb-6">Course Progress</h2>
            
            {/* Progress Stats */}
            <div className="mb-3 sm:mb-4">
              <div className="flex items-center justify-between mb-2 sm:mb-3">
                <span className="text-xs sm:text-sm font-semibold text-gray-600">Completion</span>
                <span className="text-2xl sm:text-3xl font-bold text-emerald-600">
                  {course.progress_percentage || 0}%
                </span>
              </div>
              <div className="h-2.5 sm:h-3 bg-gray-200 rounded-full overflow-hidden mb-2 sm:mb-3">
                <div
                  className="h-full bg-emerald-600 rounded-full transition-all duration-500"
                  style={{ width: `${course.progress_percentage || 0}%` }}
                />
              </div>
              <p className="text-xs sm:text-sm text-gray-600 font-medium">
                {course.lessons_completed || 0} of {course.total_lessons} lessons completed
              </p>
            </div>
          </div>

          {/* Lessons List */}
          <div className="p-3 sm:p-4 lg:p-6">
            <h3 className="text-[10px] sm:text-xs font-bold text-gray-500 uppercase tracking-wider mb-3 sm:mb-4">LESSONS</h3>
            <div className="space-y-2 sm:space-y-3">
              {course.lessons.map((lesson) => (
                <button
                  key={lesson.id}
                  onClick={() => selectLesson(lesson)}
                  className={`w-full text-left p-3 sm:p-4 rounded-lg border-2 transition-all ${
                    currentLesson.id === lesson.id
                      ? 'bg-emerald-50 border-emerald-500 shadow-sm'
                      : lesson.is_completed
                      ? 'bg-emerald-50/30 border-emerald-200 hover:border-emerald-300'
                      : 'bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm'
                  }`}
                >
                  <div className="flex items-start justify-between mb-1.5 sm:mb-2">
                    <div className="flex items-center space-x-1.5 sm:space-x-2">
                      <span className={`text-[10px] sm:text-xs font-bold px-2 py-0.5 sm:px-2.5 sm:py-1 rounded-md ${
                        currentLesson.id === lesson.id
                          ? 'bg-emerald-600 text-white'
                          : lesson.is_completed
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}>
                        {lesson.order}
                      </span>
                      {lesson.is_preview && (
                        <span className="px-2.5 py-1 bg-emerald-100 text-emerald-700 text-xs font-semibold rounded-md">
                          Free
                        </span>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      {currentLesson.id === lesson.id && (
                        <div className="w-5 h-5 bg-emerald-600 rounded-full flex items-center justify-center">
                          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                          </svg>
                        </div>
                      )}
                      {lesson.is_completed && (
                        <div className="w-5 h-5 bg-emerald-500 rounded-full flex items-center justify-center">
                          <svg className="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        </div>
                      )}
                    </div>
                  </div>
                  <h4 className={`font-semibold mb-1 text-xs sm:text-sm ${
                    currentLesson.id === lesson.id ? 'text-gray-900' : 'text-gray-700'
                  }`}>
                    {lesson.title}
                  </h4>
                  <span className={`text-[10px] sm:text-xs flex items-center font-medium ${
                    currentLesson.id === lesson.id ? 'text-emerald-700' : 'text-gray-500'
                  }`}>
                    <svg className="w-3 h-3 sm:w-3.5 sm:h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">\n                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />\n                    </svg>
                    {lesson.duration}
                  </span>
                </button>
              ))}
            </div>

            {/* Course Details */}
            <div className="mt-6 sm:mt-8 pt-5 sm:pt-6 border-t-2 border-gray-200">
              <h3 className="text-[10px] sm:text-xs font-bold text-gray-500 uppercase tracking-wider mb-3 sm:mb-4">COURSE DETAILS</h3>
              <div className="space-y-2">
                <button
                  onClick={() => router.push(`/courses/${course.slug}`)}
                  className="w-full flex items-center justify-between p-2.5 sm:p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-emerald-500 hover:bg-emerald-50 transition-all group"
                >
                  <div className="flex items-center space-x-2 sm:space-x-3">
                    <div className="w-8 h-8 sm:w-9 sm:h-9 bg-emerald-100 rounded-lg flex items-center justify-center">
                      <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <span className="font-semibold text-gray-900 text-xs sm:text-sm">Course Overview</span>
                  </div>
                  <svg className="w-4 h-4 text-gray-400 group-hover:text-emerald-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>

                <button
                  onClick={() => router.push('/my-courses')}
                  className="w-full flex items-center justify-between p-2.5 sm:p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-emerald-500 hover:bg-emerald-50 transition-all group"
                >
                  <div className="flex items-center space-x-2 sm:space-x-3">
                    <div className="w-8 h-8 sm:w-9 sm:h-9 bg-emerald-100 rounded-lg flex items-center justify-center">
                      <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                    </div>
                    <span className="font-semibold text-gray-900 text-xs sm:text-sm">My Courses</span>
                  </div>
                  <svg className="w-4 h-4 text-gray-400 group-hover:text-emerald-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Course Completion Modal */}
      {showCompletionModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-3 sm:p-4 animate-in fade-in duration-300">
          <div className="bg-white rounded-xl sm:rounded-2xl max-w-lg w-full p-5 sm:p-6 lg:p-8 shadow-2xl animate-in zoom-in duration-300">
            
            {/* Trophy Animation */}
            <div className="flex justify-center mb-4 sm:mb-5 lg:mb-6">
              <div className="relative">
                <div className="w-24 h-24 sm:w-28 sm:h-28 lg:w-32 lg:h-32 bg-emerald-600 rounded-full flex items-center justify-center shadow-xl">
                  <TrophyIcon className="w-16 h-16 sm:w-18 sm:h-18 lg:w-20 lg:h-20 text-white" />
                </div>
              </div>
            </div>

            {/* Success Message */}
            <div className="text-center mb-5 sm:mb-6 lg:mb-8">
              <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2 sm:mb-3">
                Congratulations! 🎉
              </h2>
              <p className="text-base sm:text-lg text-gray-600 mb-1 sm:mb-2">
                You've successfully completed
              </p>
              <p className="text-lg sm:text-xl font-bold text-emerald-600">
                {course?.title}
              </p>
            </div>

            {/* Stats Card */}
            <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg sm:rounded-xl p-4 sm:p-5 lg:p-6 mb-5 sm:mb-6 lg:mb-8 border border-gray-200">
              <div className="grid grid-cols-2 gap-4 sm:gap-6">
                <div className="text-center">
                  <div className="text-2xl sm:text-3xl font-bold text-gray-900 mb-1">{course?.total_lessons}</div>
                  <div className="text-xs sm:text-sm text-gray-600">Lessons Completed</div>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center space-x-1 sm:space-x-2 mb-1">
                    <CheckCircleIcon className="w-6 h-6 sm:w-7 sm:h-7 text-emerald-600" />
                    <span className="text-2xl sm:text-3xl font-bold text-emerald-600">100%</span>
                  </div>
                  <div className="text-xs sm:text-sm text-gray-600">Course Progress</div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-2 sm:space-y-3">
              <button
                onClick={() => {
                  setShowCompletionModal(false);
                  router.push('/courses');
                }}
                className="w-full px-5 py-3 sm:px-6 sm:py-4 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm sm:text-base rounded-lg transition-all shadow-lg hover:shadow-xl"
              >
                Explore More Courses
              </button>
              <button
                onClick={() => {
                  setShowCompletionModal(false);
                  router.push(`/courses/${slug}`);
                }}
                className="w-full px-5 py-3 sm:px-6 sm:py-4 bg-gray-100 hover:bg-gray-200 text-gray-900 font-semibold text-sm sm:text-base rounded-lg transition-all"
              >
                Back to Course Details
              </button>
            </div>

            {/* Close button */}
            <button
              onClick={() => {
                setShowCompletionModal(false);
                router.push(`/courses/${slug}`);
              }}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>
        </div>
      )}

      {/* Completed Toast Notification */}
      {showCompletedToast && (
        <div className="fixed top-6 right-6 z-50 animate-in slide-in-from-top duration-300">
          <div className="bg-white border-l-4 border-emerald-500 shadow-xl rounded-lg px-6 py-4 flex items-center space-x-3 max-w-md">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                <CheckCircleIcon className="w-6 h-6 text-emerald-600" />
              </div>
            </div>
            <div>
              <p className="font-semibold text-gray-900">Lesson Completed! ✨</p>
              <p className="text-sm text-gray-600">Great job! Moving to next lesson...</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
