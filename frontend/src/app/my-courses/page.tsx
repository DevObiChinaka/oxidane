'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import DashboardSidebar from '../components/DashboardSidebar';
import { apiGet } from '@/lib/api';
import MobileMenuButton from '../components/MobileMenuButton';
import { useSmartNavbar } from '../hooks/useSmartNavbar';

interface Course {
  id: string;
  title: string;
  slug: string;
  short_description: string;
  course_type: 'free' | 'premium';
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
  thumbnail: string | null;
  first_lesson_thumbnail: {
    high: string;
    medium: string;
  } | null;
  estimated_duration: number;
  total_lessons: number;
  lessons_completed: number;
  progress_percentage: number;
  enrolled_at: string | null;
}

export default function MyCoursesPage() {
  const router = useRouter();
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'in-progress' | 'completed'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const showNavbar = useSmartNavbar();

  useEffect(() => {
    checkAuthAndFetchCourses();
  }, []);

  const checkAuthAndFetchCourses = async () => {
    try {
      // Verify token is valid
      const profileResponse = await apiGet('/auth/profile/');

      if (!profileResponse.ok) {
        return;
      }

      setIsAuthenticated(true);
      await fetchEnrolledCourses();
    } catch (error) {
          }
  };

  const fetchEnrolledCourses = async () => {
    try {
      const response = await apiGet('/courses/enrolled/');

      if (!response.ok) {
        throw new Error('Failed to fetch courses');
      }

      const data = await response.json();

      setCourses(data.courses || []);
    } catch (error) {
            // Keep empty array on error
      setCourses([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredCourses = courses.filter(course => {
    // Filter by status
    if (filter === 'in-progress' && course.progress_percentage === 100) return false;
    if (filter === 'completed' && course.progress_percentage !== 100) return false;
    
    // Filter by search query
    if (searchQuery && !course.title.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    
    return true;
  });

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'beginner':
        return 'text-green-600';
      case 'intermediate':
        return 'text-amber-600';
      case 'advanced':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <DashboardSidebar 
          isMobileMenuOpen={isMobileMenuOpen}
          setIsMobileMenuOpen={setIsMobileMenuOpen}
        />
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center space-y-4">
            <div className="w-12 h-12 border-3 border-gray-200 border-t-[#00B38F] rounded-full animate-spin"></div>
            <p className="text-gray-600 text-sm">Loading courses...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <MobileMenuButton showNavbar={showNavbar} onMenuOpen={() => setIsMobileMenuOpen(true)} />

      <DashboardSidebar 
        isMobileMenuOpen={isMobileMenuOpen}
        setIsMobileMenuOpen={setIsMobileMenuOpen}
      />

      {/* Main Content */}
      <main className="flex-1 min-h-screen">
        {/* Clean Header - Mobile Optimized */}
        <header className="bg-white border-b border-gray-200 px-3 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8">
          <div className="flex flex-col gap-3 sm:gap-4">
            <div>
              <h2 className="text-xl sm:text-2xl font-semibold text-gray-900 mb-1">My Learning Journey</h2>
              <p className="text-gray-500 text-xs sm:text-sm">Track your progress and continue where you left off</p>
            </div>
            
            {/* Stats Row - Compact Mobile */}
            <div className="flex items-center gap-3 sm:gap-4 lg:gap-6 overflow-x-auto pb-2 scrollbar-hide">
              <div className="text-center px-3 sm:px-4 flex-shrink-0">
                <div className="text-xl sm:text-2xl font-bold text-[#000856]">{courses.length}</div>
                <div className="text-[10px] sm:text-xs text-gray-500 whitespace-nowrap">Enrolled</div>
              </div>
              <div className="w-px h-8 sm:h-12 bg-gray-200"></div>
              <div className="text-center px-3 sm:px-4 flex-shrink-0">
                <div className="text-xl sm:text-2xl font-bold text-green-600">{courses.filter(c => c.progress_percentage === 100).length}</div>
                <div className="text-[10px] sm:text-xs text-gray-500 whitespace-nowrap">Completed</div>
              </div>
              <div className="w-px h-8 sm:h-12 bg-gray-200"></div>
              <div className="text-center px-3 sm:px-4 flex-shrink-0">
                <div className="text-xl sm:text-2xl font-bold text-[#00B38F]">{courses.filter(c => c.progress_percentage > 0 && c.progress_percentage < 100).length}</div>
                <div className="text-[10px] sm:text-xs text-gray-500 whitespace-nowrap">In Progress</div>
              </div>
            </div>
          </div>
        </header>

        <div className="p-3 sm:p-6 lg:p-8">
          {/* Filters and Search - Mobile Optimized */}
          <div className="mb-4 sm:mb-6 lg:mb-8 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 sm:gap-4">
            <div className="flex gap-1.5 sm:gap-2 overflow-x-auto pb-2 scrollbar-hide">
              <button
                onClick={() => setFilter('all')}
                className={`px-3 sm:px-4 lg:px-5 py-2 rounded-lg font-medium text-xs sm:text-sm whitespace-nowrap transition-colors ${
                  filter === 'all'
                    ? 'bg-gray-100 text-gray-900 border border-gray-200'
                    : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                }`}
              >
                All Courses
              </button>
              <button
                onClick={() => setFilter('in-progress')}
                className={`px-3 sm:px-4 lg:px-5 py-2 rounded-lg font-medium text-xs sm:text-sm whitespace-nowrap transition-colors ${
                  filter === 'in-progress'
                    ? 'bg-gray-100 text-gray-900 border border-gray-200'
                    : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                }`}
              >
                In Progress
              </button>
              <button
                onClick={() => setFilter('completed')}
                className={`px-3 sm:px-4 lg:px-5 py-2 rounded-lg font-medium text-xs sm:text-sm whitespace-nowrap transition-colors ${
                  filter === 'completed'
                    ? 'bg-gray-100 text-gray-900 border border-gray-200'
                    : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                }`}
              >
                Completed
              </button>
            </div>

            <div className="relative w-full sm:w-auto">
              <input
                type="text"
                placeholder="Search courses..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="px-4 py-2 sm:py-2.5 pl-9 sm:pl-10 bg-white border border-gray-200 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-200 focus:border-transparent w-full sm:w-80 text-xs sm:text-sm"
              />
              <svg
                className="w-4 h-4 sm:w-5 sm:h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>

          {/* Courses Grid - Mobile Optimized */}
          {filteredCourses.length === 0 ? (
            <div className="bg-white border border-gray-200 rounded-lg p-8 sm:p-12 text-center max-w-md mx-auto">
              <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-gray-50 flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 sm:w-10 sm:h-10 text-[#000856]"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2">No courses found</h3>
              <p className="text-gray-500 mb-6 text-xs sm:text-sm">Start your learning journey today</p>
              <button
                onClick={() => router.push('/courses')}
                className="px-6 py-2.5 bg-[#00B38F] hover:bg-[#00A87D] text-white rounded-lg transition-colors text-sm font-medium"
              >
                Browse Courses
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4 lg:gap-6">
              {filteredCourses.map((course) => (
                <div
                  key={course.id}
                  className="group bg-white border border-gray-200 rounded-xl hover:shadow-lg transition-all cursor-pointer overflow-hidden"
                  onClick={() => router.push(`/courses/${course.slug}`)}
                >
                  <div className="p-3 sm:p-4 lg:p-6">
                    {/* Header Row - Compact Mobile */}
                    <div className="flex items-start justify-between mb-3 sm:mb-4 gap-3">
                      <div className="flex items-start gap-2.5 sm:gap-3 lg:gap-4 flex-1 min-w-0">
                        {/* Course Icon - Smaller on Mobile */}
                        <div className="w-10 h-10 sm:w-12 sm:h-12 lg:w-14 lg:h-14 rounded-xl bg-gray-50 flex items-center justify-center flex-shrink-0">
                          <svg
                            className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7 text-[#000856]"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                          </svg>
                        </div>
                        
                        {/* Title & Badge */}
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm sm:text-base lg:text-lg font-semibold text-gray-900 group-hover:text-[#000856] transition-colors line-clamp-2 mb-1.5 sm:mb-2">
                            {course.title}
                          </h3>
                          <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                            <span className={`text-[10px] sm:text-xs font-medium uppercase tracking-wide ${getLevelColor(course.difficulty_level)}`}>
                              {course.difficulty_level}
                            </span>
                            {course.course_type === 'premium' && (
                              <span className="text-[10px] sm:text-xs font-medium uppercase tracking-wide text-purple-600">
                                Premium
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Progress Circle - Compact Mobile */}
                      <div className="flex-shrink-0">
                        <div className="relative w-10 h-10 sm:w-12 sm:h-12 lg:w-14 lg:h-14">
                          <svg className="w-10 h-10 sm:w-12 sm:h-12 lg:w-14 lg:h-14 transform -rotate-90">
                            <circle
                              cx="20"
                              cy="20"
                              r="18"
                              stroke="currentColor"
                              strokeWidth="3"
                              fill="none"
                              className="text-gray-100 sm:hidden"
                            />
                            <circle
                              cx="24"
                              cy="24"
                              r="20"
                              stroke="currentColor"
                              strokeWidth="3.5"
                              fill="none"
                              className="text-gray-100 hidden sm:block lg:hidden"
                            />
                            <circle
                              cx="28"
                              cy="28"
                              r="24"
                              stroke="currentColor"
                              strokeWidth="4"
                              fill="none"
                              className="text-gray-100 hidden lg:block"
                            />
                            <circle
                              cx="20"
                              cy="20"
                              r="18"
                              stroke="currentColor"
                              strokeWidth="3"
                              fill="none"
                              strokeDasharray={`${2 * Math.PI * 18}`}
                              strokeDashoffset={`${2 * Math.PI * 18 * (1 - course.progress_percentage / 100)}`}
                              className={`${course.progress_percentage === 100 ? 'text-green-500' : 'text-[#00B38F]'} sm:hidden`}
                              strokeLinecap="round"
                            />
                            <circle
                              cx="24"
                              cy="24"
                              r="20"
                              stroke="currentColor"
                              strokeWidth="3.5"
                              fill="none"
                              strokeDasharray={`${2 * Math.PI * 20}`}
                              strokeDashoffset={`${2 * Math.PI * 20 * (1 - course.progress_percentage / 100)}`}
                              className={`${course.progress_percentage === 100 ? 'text-green-500' : 'text-[#00B38F]'} hidden sm:block lg:hidden`}
                              strokeLinecap="round"
                            />
                            <circle
                              cx="28"
                              cy="28"
                              r="24"
                              stroke="currentColor"
                              strokeWidth="4"
                              fill="none"
                              strokeDasharray={`${2 * Math.PI * 24}`}
                              strokeDashoffset={`${2 * Math.PI * 24 * (1 - course.progress_percentage / 100)}`}
                              className={`${course.progress_percentage === 100 ? 'text-green-500' : 'text-[#00B38F]'} hidden lg:block`}
                              strokeLinecap="round"
                            />
                          </svg>
                          <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-[10px] sm:text-xs font-bold text-gray-900">{course.progress_percentage}%</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Description - Hidden on Mobile */}
                    <p className="hidden sm:block text-xs sm:text-sm text-gray-600 mb-3 sm:mb-4 line-clamp-2">{course.short_description}</p>

                    {/* Stats Row - Compact Mobile */}
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pt-2.5 sm:pt-3 lg:pt-4 border-t border-gray-100 gap-2 sm:gap-3">
                      <div className="flex items-center gap-2.5 sm:gap-3 lg:gap-4 text-[10px] sm:text-xs lg:text-sm text-gray-500 flex-wrap">
                        <div className="flex items-center gap-1 sm:gap-1.5">
                          <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
                          </svg>
                          <span>{course.lessons_completed}/{course.total_lessons} lessons</span>
                        </div>
                        <div className="flex items-center gap-1 sm:gap-1.5">
                          <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span>{course.estimated_duration}</span>
                        </div>
                      </div>

                      {/* Action Button - Full width on Mobile */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/courses/${course.slug}/watch`);
                        }}
                        className={`w-full sm:w-auto px-3 sm:px-4 lg:px-5 py-2 rounded-lg transition-colors flex items-center justify-center gap-1.5 sm:gap-2 text-xs sm:text-sm font-medium whitespace-nowrap ${
                          course.progress_percentage === 100
                            ? 'bg-green-50 text-green-700 hover:bg-green-100'
                            : 'bg-[#00B38F] text-white hover:bg-[#00A87D]'
                        }`}
                      >
                        {course.progress_percentage === 100 ? (
                          <>
                            <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Review
                          </>
                        ) : (
                          <>
                            <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M8 5v14l11-7z"/>
                            </svg>
                            Continue
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
