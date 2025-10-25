'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams, useSearchParams } from 'next/navigation';

interface Lesson {
  id: number;
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
  id: number;
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

  useEffect(() => {
    if (slug) {
      checkAuthAndFetchCourse();
    }
  }, [slug]);

  useEffect(() => {
    if (course && course.lessons.length > 0) {
      if (lessonIdParam) {
        const lesson = course.lessons.find(l => l.id === parseInt(lessonIdParam));
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

  const checkAuthAndFetchCourse = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        router.push('/auth/login');
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
        router.push('/auth/login');
        return;
      }

      setIsAuthenticated(true);
      await fetchCourseAndLessons();
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      router.push('/auth/login');
    }
  };

  const fetchCourseAndLessons = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/auth/login');
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

        setCourse(data);
      } else if (response.status === 401) {
        router.push('/auth/login');
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
      router.push('/auth/login');
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
        // Update local state
        const updatedLessons = course.lessons.map(l =>
          l.id === currentLesson.id ? { ...l, is_completed: true } : l
        );
        setCourse({ ...course, lessons: updatedLessons });
        
        // Move to next lesson if available
        const currentIndex = course.lessons.findIndex(l => l.id === currentLesson.id);
        if (currentIndex < course.lessons.length - 1) {
          const nextLesson = updatedLessons[currentIndex + 1];
          setCurrentLesson(nextLesson);
          router.push(`/courses/${slug}/watch?lesson=${nextLesson.id}`, { scroll: false });
        } else {
          // Course completed
          alert('Congratulations! You have completed this course!');
        }
      } else if (response.status === 401) {
        router.push('/auth/login');
      } else {
        console.error('Failed to mark lesson as complete');
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

  const getVideoPlayer = () => {
    if (!currentLesson) return null;

    if (currentLesson.video_source === 'youtube' && currentLesson.youtube_video_id) {
      return (
        <iframe
          src={`https://www.youtube.com/embed/${currentLesson.youtube_video_id}?autoplay=1`}
          className="w-full h-full"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      );
    } else if (currentLesson.video_source === 'vimeo' && currentLesson.video_url) {
      const vimeoId = currentLesson.video_url.split('/').pop();
      return (
        <iframe
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
          <div className="bg-black aspect-video lg:h-[60vh] m-4 rounded-xl shadow-lg overflow-hidden">
            {getVideoPlayer()}
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
    </div>
  );
}
