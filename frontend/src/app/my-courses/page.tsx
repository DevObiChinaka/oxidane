'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import DashboardSidebar from '../components/DashboardSidebar';
import { apiGet } from '@/lib/api';

interface Course {
  id: string;
  title: string;
  slug: string;
  short_description: string;
  course_type: 'free' | 'premium';
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
  thumbnail: string | null;
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
      console.error('Auth check failed:', error);
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
      console.error('Courses fetch failed:', error);
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
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsMobileMenuOpen(true)}
        className="lg:hidden fixed top-4 left-4 z-30 p-2 bg-white rounded-lg shadow-lg border border-gray-200 hover:bg-gray-50 transition-colors"
      >
        <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <DashboardSidebar 
        isMobileMenuOpen={isMobileMenuOpen}
        setIsMobileMenuOpen={setIsMobileMenuOpen}
      />

      {/* Main Content */}
      <main className="flex-1 min-h-screen">
        {/* Clean Header */}
        <header className="bg-white border-b border-gray-200 px-4 sm:px-6 lg:px-8 py-6 lg:py-8">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
            <div className="ml-12 lg:ml-0">
              <h2 className="text-xl sm:text-2xl font-semibold text-gray-900 mb-1 sm:mb-2">My Learning Journey</h2>
              <p className="text-gray-500 text-sm">Track your progress and continue where you left off</p>
            </div>
            <div className="hidden sm:flex items-center gap-4 lg:gap-6">
              <div className="text-center px-4">
                <div className="text-2xl font-bold text-[#000856]">{courses.length}</div>
                <div className="text-xs text-gray-500">Enrolled</div>
              </div>
              <div className="w-px h-12 bg-gray-200"></div>
              <div className="text-center px-4">
                <div className="text-2xl font-bold text-green-600">{courses.filter(c => c.progress_percentage === 100).length}</div>
                <div className="text-xs text-gray-500">Completed</div>
              </div>
              <div className="w-px h-12 bg-gray-200"></div>
              <div className="text-center px-4">
                <div className="text-2xl font-bold text-[#00B38F]">{courses.filter(c => c.progress_percentage > 0 && c.progress_percentage < 100).length}</div>
                <div className="text-xs text-gray-500">In Progress</div>
              </div>
            </div>
          </div>
        </header>

        <div className="p-4 sm:p-6 lg:p-8">
          {/* Filters and Search */}
          <div className="mb-6 lg:mb-8 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setFilter('all')}
                className={`px-4 sm:px-5 py-2 sm:py-2.5 rounded-lg font-medium text-sm transition-colors ${
                  filter === 'all'
                    ? 'bg-gray-100 text-gray-900 border border-gray-200'
                    : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                }`}
              >
                All Courses
              </button>
              <button
                onClick={() => setFilter('in-progress')}
                className={`px-4 sm:px-5 py-2 sm:py-2.5 rounded-lg font-medium text-sm transition-colors ${
                  filter === 'in-progress'
                    ? 'bg-gray-100 text-gray-900 border border-gray-200'
                    : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                }`}
              >
                In Progress
              </button>
              <button
                onClick={() => setFilter('completed')}
                className={`px-4 sm:px-5 py-2 sm:py-2.5 rounded-lg font-medium text-sm transition-colors ${
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
                className="px-4 py-2.5 pl-10 bg-white border border-gray-200 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-200 focus:border-transparent w-full sm:w-80 text-sm"
              />
              <svg
                className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>

          {/* Courses Grid */}
          {filteredCourses.length === 0 ? (
            <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
              <div className="w-20 h-20 rounded-full bg-gray-50 flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-10 h-10 text-[#000856]"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No courses found</h3>
              <p className="text-gray-500 mb-6 text-sm">Start your learning journey today</p>
              <button
                onClick={() => router.push('/courses')}
                className="px-6 py-2.5 bg-[#00B38F] hover:bg-[#00A87D] text-white rounded-lg transition-colors text-sm font-medium"
              >
                Browse Courses
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
              {filteredCourses.map((course) => (
                <div
                  key={course.id}
                  className="group bg-white border border-gray-200 rounded-xl hover:shadow-lg transition-all cursor-pointer overflow-hidden"
                  onClick={() => router.push(`/courses/${course.slug}`)}
                >
                  <div className="p-4 sm:p-6">
                    {/* Header Row */}
                    <div className="flex flex-col sm:flex-row items-start justify-between mb-4 gap-4">
                      <div className="flex items-start gap-3 sm:gap-4 flex-1 w-full">
                        {/* Course Icon - Navy book icon */}
                        <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-gray-50 flex items-center justify-center flex-shrink-0">
                          <svg
                            className="w-6 h-6 sm:w-7 sm:h-7 text-[#000856]"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                          </svg>
                        </div>
                        
                        {/* Title & Badge */}
                        <div className="flex-1 min-w-0">
                          <h3 className="text-base sm:text-lg font-semibold text-gray-900 group-hover:text-[#000856] transition-colors line-clamp-2 mb-2">
                            {course.title}
                          </h3>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className={`text-xs font-medium uppercase tracking-wide ${getLevelColor(course.difficulty_level)}`}>
                              {course.difficulty_level}
                            </span>
                            {course.course_type === 'premium' && (
                              <span className="text-xs font-medium uppercase tracking-wide text-purple-600">
                                Premium
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Progress Circle */}
                      <div className="flex-shrink-0">
                        <div className="relative w-12 h-12 sm:w-14 sm:h-14">
                          <svg className="w-12 h-12 sm:w-14 sm:h-14 transform -rotate-90">
                            <circle
                              cx="28"
                              cy="28"
                              r="24"
                              stroke="currentColor"
                              strokeWidth="4"
                              fill="none"
                              className="text-gray-100"
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
                              className={course.progress_percentage === 100 ? 'text-green-500' : 'text-[#00B38F]'}
                              strokeLinecap="round"
                            />
                          </svg>
                          <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-xs font-bold text-gray-900">{course.progress_percentage}%</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Description */}
                    <p className="text-sm text-gray-600 mb-4 line-clamp-2">{course.short_description}</p>

                    {/* Stats Row */}
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pt-4 border-t border-gray-100 gap-3">
                      <div className="flex items-center gap-3 sm:gap-4 text-xs sm:text-sm text-gray-500 flex-wrap">
                        <div className="flex items-center gap-1.5">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
                          </svg>
                          <span>{course.lessons_completed}/{course.total_lessons} lessons</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span>{course.estimated_duration}</span>
                        </div>
                      </div>

                      {/* Action Button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/courses/${course.slug}/watch`);
                        }}
                        className={`px-3 sm:px-4 py-2 rounded-lg transition-colors flex items-center gap-1.5 sm:gap-2 text-xs sm:text-sm font-medium whitespace-nowrap ${
                          course.progress_percentage === 100
                            ? 'bg-green-50 text-green-700 hover:bg-green-100'
                            : 'bg-[#00B38F] text-white hover:bg-[#00A87D]'
                        }`}
                      >
                        {course.progress_percentage === 100 ? (
                          <>
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Review
                          </>
                        ) : (
                          <>
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
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
