'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams, useSearchParams } from 'next/navigation';
import { CheckCircleIcon, XMarkIcon, TrophyIcon } from '@heroicons/react/24/solid';

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

  useEffect(() => {
    if (slug) {
      checkAuthAndFetchCourse();
    }
  }, [slug]);

  // Re-fetch course data when lesson changes to get updated completion states
  useEffect(() => {
    if (slug && lessonIdParam) {
      fetchCourseAndLessons();
    }
  }, [lessonIdParam]);

  useEffect(() => {
    if (course && course.lessons.length > 0) {
      if (lessonIdParam) {
        // Compare as strings since IDs are UUIDs
        const lesson = course.lessons.find(l => l.id === lessonIdParam);
        if (lesson) {
          setCurrentLesson(lesson);
        } else {
          setCurrentLesson(course.lessons[0]);
        }
      } else {
        // Find first incomplete lesson or first lesson
        const firstIncomplete = course.lessons.find(l => !l.is_completed);
        setCurrentLesson(firstIncomplete || course.lessons[0]);
      }
    }
  }, [course, lessonIdParam]);

  // Setup YouTube and Vimeo player event listeners
  useEffect(() => {
    if (!currentLesson) return;

    // YouTube Player API
    if (currentLesson.video_source === 'youtube') {
      // Load YouTube IFrame API
      if (!(window as any).YT) {
        const tag = document.createElement('script');
        tag.src = 'https://www.youtube.com/iframe_api';
        const firstScriptTag = document.getElementsByTagName('script')[0];
        firstScriptTag.parentNode?.insertBefore(tag, firstScriptTag);
      }

      // Initialize player when API is ready
      (window as any).onYouTubeIframeAPIReady = () => {
        const player = new (window as any).YT.Player('youtube-player', {
          events: {
            'onStateChange': (event: any) => {
              // 0 = ended
              if (event.data === 0) {
                handleVideoEnd();
              }
            }
          }
        });
      };

      // If API already loaded, initialize immediately
      if ((window as any).YT && (window as any).YT.Player) {
        setTimeout(() => {
          const player = new (window as any).YT.Player('youtube-player', {
            events: {
              'onStateChange': (event: any) => {
                if (event.data === 0) {
                  handleVideoEnd();
                }
              }
            }
          });
        }, 1000);
      }
    }

    // Vimeo Player API
    if (currentLesson.video_source === 'vimeo') {
      // Load Vimeo Player API
      if (!(window as any).Vimeo) {
        const script = document.createElement('script');
        script.src = 'https://player.vimeo.com/api/player.js';
        document.head.appendChild(script);
        
        script.onload = () => {
          const iframe = document.getElementById('vimeo-player');
          if (iframe && (window as any).Vimeo) {
            const player = new (window as any).Vimeo.Player(iframe);
            player.on('ended', handleVideoEnd);
          }
        };
      } else {
        const iframe = document.getElementById('vimeo-player');
        if (iframe) {
          const player = new (window as any).Vimeo.Player(iframe);
          player.on('ended', handleVideoEnd);
        }
      }
    }
  }, [currentLesson]);

  const checkAuthAndFetchCourse = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      if (!token) {
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
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        router.push('/auth');
        return;
      }

      setIsAuthenticated(true);
      await fetchCourseAndLessons();
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      router.push('/auth');
    }
  };

  const fetchCourseAndLessons = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/auth');
        return;
      }

      const response = await fetch(`http://localhost:8000/api/courses/${slug}/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

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
      } else if (response.status === 401 || response.status === 403) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        router.push('/auth');
      } else if (response.status === 404) {
        setError('Course not found');
      } else {
        setError('Failed to load course');
      }
    } catch (err) {
      console.error('Error fetching course:', err);
      setError('Failed to load course');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkComplete = async () => {
    if (!currentLesson || !course) return;

    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/auth');
      return;
    }

    try {
      setMarking(true);
      const response = await fetch(
        `http://localhost:8000/api/courses/lessons/${currentLesson.id}/progress/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            is_completed: true,
            time_spent: 0, // You could track actual time spent
          }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        console.log('Progress update response:', data);
        
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
      } else if (response.status === 401 || response.status === 403) {
        // Unauthorized or Forbidden - redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        router.push('/auth');
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error('Failed to mark lesson as complete:', errorData);
        alert('Failed to mark lesson as complete. Please try again.');
      }
    } catch (err) {
      console.error('Error marking lesson complete:', err);
    } finally {
      setMarking(false);
    }
  };

  const selectLesson = (lesson: Lesson) => {
    setCurrentLesson(lesson);
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

    if (currentLesson.video_source === 'youtube' && currentLesson.youtube_video_id) {
      return (
        <iframe
          id="youtube-player"
          src={`https://www.youtube.com/embed/${currentLesson.youtube_video_id}?autoplay=1&enablejsapi=1`}
          className="w-full h-full"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      );
    } else if (currentLesson.video_source === 'vimeo' && currentLesson.video_url) {
      const vimeoId = currentLesson.video_url.split('/').pop();
      return (
        <iframe
          id="vimeo-player"
          src={`https://player.vimeo.com/video/${vimeoId}?autoplay=1`}
          className="w-full h-full"
          allow="autoplay; fullscreen; picture-in-picture"
          allowFullScreen
        />
      );
    } else if (currentLesson.video_url) {
      return (
        <video
          src={currentLesson.video_url}
          controls
          autoPlay
          className="w-full h-full"
          onEnded={handleVideoEnd}
        />
      );
    }

    return (
      <div className="w-full h-full flex items-center justify-center bg-slate-800">
        <p className="text-slate-400">No video available</p>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#000856] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#00B38F]"></div>
      </div>
    );
  }

  if (error || !course || !currentLesson) {
    return (
      <div className="min-h-screen bg-[#000856] flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-white mb-4">{error || 'Content not available'}</h2>
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
    <div className="min-h-screen bg-[#000856]">
      <div className="flex flex-col lg:flex-row h-screen">
        {/* Main Video Area */}
        <div className="flex-1 flex flex-col">
          {/* Video Player */}
          <div className="bg-black aspect-video lg:h-[60vh] m-4 rounded-xl shadow-lg overflow-hidden relative">
            {getVideoPlayer()}
            
            {/* Auto-Advance Notification */}
            {showAutoAdvanceNotification && (
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-6">
                <div className="max-w-2xl mx-auto bg-slate-800/95 backdrop-blur-sm rounded-lg p-4 border border-[#00B38F]/30 shadow-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="relative">
                        <svg className="w-10 h-10 transform -rotate-90">
                          <circle
                            cx="20"
                            cy="20"
                            r="16"
                            stroke="#334155"
                            strokeWidth="3"
                            fill="none"
                          />
                          <circle
                            cx="20"
                            cy="20"
                            r="16"
                            stroke="#00B38F"
                            strokeWidth="3"
                            fill="none"
                            strokeDasharray={`${2 * Math.PI * 16}`}
                            strokeDashoffset={`${2 * Math.PI * 16 * (1 - autoAdvanceCountdown / 5)}`}
                            className="transition-all duration-1000 ease-linear"
                          />
                        </svg>
                        <span className="absolute inset-0 flex items-center justify-center text-white text-sm font-bold">
                          {autoAdvanceCountdown}
                        </span>
                      </div>
                      <div>
                        <p className="text-white font-medium">Next lesson starting soon...</p>
                        <p className="text-slate-400 text-sm">Auto-advancing in {autoAdvanceCountdown} seconds</p>
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        setShowAutoAdvanceNotification(false);
                        setAutoAdvanceCountdown(5);
                      }}
                      className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-all text-sm font-medium"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Video Info */}
          <div className="flex-1 p-6 overflow-y-auto">
            <div className="max-w-4xl">
              {/* Breadcrumb */}
              <div className="flex items-center space-x-2 text-sm text-slate-400 mb-4">
                <button
                  onClick={() => router.push('/courses')}
                  className="hover:text-white transition-colors"
                >
                  Courses
                </button>
                <span>/</span>
                <button
                  onClick={() => router.push(`/courses/${course.slug}`)}
                  className="hover:text-white transition-colors"
                >
                  {course.title}
                </button>
                <span>/</span>
                <span className="text-white">Lesson {currentLesson.order}</span>
              </div>

              {/* Lesson Title */}
              <h1 className="text-3xl font-bold text-white mb-4">{currentLesson.title}</h1>

              {/* Lesson Actions */}
              <div className="flex items-center space-x-4 mb-6">
                {!currentLesson.is_completed && (
                  <button
                    onClick={handleMarkComplete}
                    disabled={marking}
                    className="px-6 py-3 bg-[#00B38F] hover:bg-[#00A87D] text-white rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                  >
                    {marking ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white"></div>
                        <span>Marking...</span>
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Mark as Complete</span>
                      </>
                    )}
                  </button>
                )}
                {currentLesson.is_completed && (
                  <div className="flex items-center space-x-2 text-[#00B38F]">
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="font-medium">Completed</span>
                  </div>
                )}
              </div>

              {/* Lesson Description */}
              <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6">
                <h2 className="text-xl font-bold text-white mb-4">About This Lesson</h2>
                <p className="text-slate-300 whitespace-pre-line">{currentLesson.description}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar - Lesson List */}
        <div className="lg:w-96 bg-slate-900/50 backdrop-blur-sm border-l border-slate-700/50 overflow-y-auto">
          <div className="p-6">
            {/* Course Progress */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-lg font-bold text-white">Course Progress</h2>
                <span className="text-sm font-medium text-[#00B38F]">
                  {course.progress_percentage || 0}%
                </span>
              </div>
              <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden mb-2">
                <div
                  className="h-full bg-gradient-to-r from-[#00B38F] to-[#00D4A3] rounded-full transition-all"
                  style={{ width: `${course.progress_percentage || 0}%` }}
                />
              </div>
              <p className="text-xs text-slate-400">
                {course.lessons_completed || 0} of {course.total_lessons} lessons completed
              </p>
            </div>

            {/* Lessons List */}
            <div>
              <h3 className="text-sm font-medium text-slate-400 mb-3">LESSONS</h3>
              <div className="space-y-2">
                {course.lessons.map((lesson) => (
                  <button
                    key={lesson.id}
                    onClick={() => selectLesson(lesson)}
                    className={`w-full text-left p-4 rounded-lg border transition-all ${
                      currentLesson.id === lesson.id
                        ? 'bg-[#00B38F]/20 border-[#00B38F] text-white'
                        : lesson.is_completed
                        ? 'bg-slate-800/50 border-slate-700/50 text-slate-300 hover:border-slate-600'
                        : 'bg-slate-800/30 border-slate-700/30 text-slate-400 hover:border-slate-600'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-xs font-medium">Lesson {lesson.order}</span>
                      <div className="flex items-center space-x-2">
                        {lesson.is_preview && (
                          <span className="px-2 py-0.5 bg-[#00B38F]/20 text-[#00B38F] text-xs rounded-full">
                            Preview
                          </span>
                        )}
                        {lesson.is_completed && (
                          <svg className="w-4 h-4 text-[#00B38F]" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                        )}
                      </div>
                    </div>
                    <h4 className="font-medium mb-1">{lesson.title}</h4>
                    <div className="flex items-center justify-between">
                      <span className="text-xs">{lesson.duration}</span>
                      {currentLesson.id === lesson.id && (
                        <svg className="w-4 h-4 text-[#00B38F]" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                        </svg>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="mt-6 pt-6 border-t border-slate-700/50">
              <button
                onClick={() => router.push(`/courses/${course.slug}`)}
                className="w-full px-4 py-3 bg-slate-800/50 hover:bg-slate-800 text-white rounded-lg transition-all mb-2"
              >
                Course Details
              </button>
              <button
                onClick={() => router.push('/my-courses')}
                className="w-full px-4 py-3 bg-slate-800/50 hover:bg-slate-800 text-white rounded-lg transition-all"
              >
                My Courses
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Course Completion Modal */}
      {showCompletionModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl max-w-md w-full p-8 border border-[#00B38F]/30 shadow-2xl animate-in fade-in zoom-in duration-300">
            {/* Close Button */}
            <button
              onClick={() => {
                setShowCompletionModal(false);
                router.push(`/courses/${slug}`);
              }}
              className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>

            {/* Trophy Icon */}
            <div className="flex justify-center mb-6">
              <div className="relative">
                <div className="absolute inset-0 bg-[#00B38F]/30 blur-2xl rounded-full animate-pulse" />
                <div className="relative bg-gradient-to-br from-[#00B38F] to-[#00D4A3] p-6 rounded-full">
                  <TrophyIcon className="w-16 h-16 text-white" />
                </div>
              </div>
            </div>

            {/* Congratulations Text */}
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-white mb-3">
                Congratulations! 🎉
              </h2>
              <p className="text-lg text-slate-300 mb-2">
                You've completed
              </p>
              <p className="text-xl font-semibold text-[#00B38F]">
                {course?.title}
              </p>
            </div>

            {/* Stats */}
            <div className="bg-slate-800/50 rounded-lg p-4 mb-6 border border-slate-700/50">
              <div className="flex items-center justify-between mb-3">
                <span className="text-slate-400">Lessons Completed</span>
                <span className="text-white font-semibold">{course?.total_lessons}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Course Progress</span>
                <div className="flex items-center space-x-2">
                  <CheckCircleIcon className="w-5 h-5 text-[#00B38F]" />
                  <span className="text-[#00B38F] font-semibold">100%</span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-3">
              <button
                onClick={() => {
                  setShowCompletionModal(false);
                  router.push('/courses');
                }}
                className="w-full px-6 py-3 bg-gradient-to-r from-[#00B38F] to-[#00D4A3] hover:from-[#00A380] hover:to-[#00C494] text-white font-medium rounded-lg transition-all shadow-lg hover:shadow-[#00B38F]/25"
              >
                Explore More Courses
              </button>
              <button
                onClick={() => {
                  setShowCompletionModal(false);
                  router.push(`/courses/${slug}`);
                }}
                className="w-full px-6 py-3 bg-slate-700/50 hover:bg-slate-700 text-white font-medium rounded-lg transition-all border border-slate-600/50"
              >
                View Course Details
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Completed Toast Notification */}
      {showCompletedToast && (
        <div className="fixed top-6 right-6 z-50 animate-in slide-in-from-top duration-300">
          <div className="bg-gradient-to-r from-[#00B38F] to-[#00D4A3] text-white px-6 py-4 rounded-lg shadow-2xl flex items-center space-x-3 border border-white/20">
            <CheckCircleIcon className="w-6 h-6 flex-shrink-0" />
            <div>
              <p className="font-semibold">Lesson Completed! ✨</p>
              <p className="text-sm text-white/90">Great job! Moving to next lesson...</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
