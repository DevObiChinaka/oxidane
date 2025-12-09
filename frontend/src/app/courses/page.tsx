'use client';

// Force Vercel rebuild - YouTube thumbnails deployed 2025-12-09

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
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
  is_enrolled: boolean;
  can_access: boolean;
  requires_subscription: boolean;
  progress_percentage: number;
}

export default function CoursesPage() {
  const router = useRouter();
  const [courses, setCourses] = useState<Course[]>([]);
  const [filteredCourses, setFilteredCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const showNavbar = useSmartNavbar();

  useEffect(() => {
    fetchCourses();
  }, []);

  useEffect(() => {
    filterCourses();
  }, [courses, searchQuery, difficultyFilter, typeFilter]);

  const fetchCourses = async () => {
    try {
      const response = await apiGet('/courses/');
      if (response.ok) {
        const data = await response.json();
        setCourses(data.courses || []);
      }
    } catch (error) {
      console.error('Failed to fetch courses:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterCourses = () => {
    let filtered = [...courses];

    if (searchQuery) {
      filtered = filtered.filter(course =>
        course.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        course.short_description.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    if (difficultyFilter !== 'all') {
      filtered = filtered.filter(course => course.difficulty_level === difficultyFilter);
    }

    if (typeFilter !== 'all') {
      filtered = filtered.filter(course => course.course_type === typeFilter);
    }

    setFilteredCourses(filtered);
  };

  const handleCourseClick = (course: Course) => {
    router.push(`/courses/${course.slug}`);
  };

  const getCourseThumbnail = (course: Course) => {
    // Priority 1: YouTube auto-generated thumbnail from first lesson
    if (course.first_lesson_thumbnail?.high) {
      return course.first_lesson_thumbnail.high;
    }
    
    // Priority 2: Manually uploaded thumbnail
    if (course.thumbnail) {
      return course.thumbnail;
    }
    
    // Priority 3: No thumbnail - will show placeholder
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
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#00B38F]"></div>
            <p className="text-gray-600">Loading courses...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50 overflow-x-hidden">
      <DashboardSidebar 
        isMobileMenuOpen={isMobileMenuOpen}
        setIsMobileMenuOpen={setIsMobileMenuOpen}
      />

      {/* Main Content */}
      <main className="flex-1 min-h-screen w-full overflow-x-hidden">
        <MobileMenuButton showNavbar={showNavbar} onMenuOpen={() => setIsMobileMenuOpen(true)} />

        {/* Header */}
        <header className="bg-white border-b border-gray-200">
          <div className="px-4 sm:px-6 lg:px-8 py-6 lg:py-8">
            <div className="max-w-7xl mx-auto">
              {/* Title and Count */}
              <div className="mb-6">
                <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Discover Courses</h1>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-sm text-gray-500">Found</span>
                  <span className="px-2.5 py-0.5 bg-[#00B38F]/10 text-[#00B38F] rounded-full font-semibold text-sm">
                    {filteredCourses.length}
                  </span>
                  <span className="text-sm text-gray-500">{filteredCourses.length === 1 ? 'course' : 'courses'}</span>
                </div>
              </div>

              {/* Search and Filters Container */}
              <div className="space-y-4">
                {/* Search Bar */}
                <div className="relative max-w-2xl">
                  <input
                    type="text"
                    placeholder="Search courses by title or description..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full px-4 py-3 pl-11 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#00B38F] focus:border-transparent transition-all"
                  />
                  <svg 
                    className="w-5 h-5 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  {searchQuery && (
                    <button
                      onClick={() => setSearchQuery('')}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>

                {/* Filters Row */}
                <div className="flex flex-col sm:flex-row gap-3">
                  {/* Difficulty Filter */}
                  <div className="flex-1">
                    <label className="block text-xs font-medium text-gray-700 mb-2">Difficulty Level</label>
                    <div className="flex gap-2 overflow-x-auto pb-1 hide-scrollbar">
                      <button 
                        onClick={() => setDifficultyFilter('all')} 
                        className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                          difficultyFilter === 'all' 
                            ? 'bg-[#00B38F] text-white shadow-sm' 
                            : 'bg-white text-gray-600 border border-gray-200 hover:border-[#00B38F]'
                        }`}
                      >
                        All Levels
                      </button>
                      <button 
                        onClick={() => setDifficultyFilter('beginner')} 
                        className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                          difficultyFilter === 'beginner' 
                            ? 'bg-[#00B38F] text-white shadow-sm' 
                            : 'bg-white text-gray-600 border border-gray-200 hover:border-[#00B38F]'
                        }`}
                      >
                        Beginner
                      </button>
                      <button 
                        onClick={() => setDifficultyFilter('intermediate')} 
                        className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                          difficultyFilter === 'intermediate' 
                            ? 'bg-[#00B38F] text-white shadow-sm' 
                            : 'bg-white text-gray-600 border border-gray-200 hover:border-[#00B38F]'
                        }`}
                      >
                        Intermediate
                      </button>
                      <button 
                        onClick={() => setDifficultyFilter('advanced')} 
                        className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                          difficultyFilter === 'advanced' 
                            ? 'bg-[#00B38F] text-white shadow-sm' 
                            : 'bg-white text-gray-600 border border-gray-200 hover:border-[#00B38F]'
                        }`}
                      >
                        Advanced
                      </button>
                    </div>
                  </div>

                  {/* Type Filter */}
                  <div className="flex-1">
                    <label className="block text-xs font-medium text-gray-700 mb-2">Course Type</label>
                    <div className="flex gap-2 overflow-x-auto pb-1 hide-scrollbar">
                      <button 
                        onClick={() => setTypeFilter('all')} 
                        className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                          typeFilter === 'all' 
                            ? 'bg-[#00B38F] text-white shadow-sm' 
                            : 'bg-white text-gray-600 border border-gray-200 hover:border-[#00B38F]'
                        }`}
                      >
                        All Courses
                      </button>
                      <button 
                        onClick={() => setTypeFilter('free')} 
                        className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                          typeFilter === 'free' 
                            ? 'bg-[#00B38F] text-white shadow-sm' 
                            : 'bg-white text-gray-600 border border-gray-200 hover:border-[#00B38F]'
                        }`}
                      >
                        Free
                      </button>
                      <button 
                        onClick={() => setTypeFilter('premium')} 
                        className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                          typeFilter === 'premium' 
                            ? 'bg-[#00B38F] text-white shadow-sm' 
                            : 'bg-white text-gray-600 border border-gray-200 hover:border-[#00B38F]'
                        }`}
                      >
                        Premium
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Courses Grid */}
        <div className="p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">
          {filteredCourses.length === 0 ? (
            <div className="max-w-md mx-auto bg-white border border-gray-200 rounded-xl p-8 sm:p-12 text-center">
              <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 sm:w-10 sm:h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2">No courses found</h3>
              <p className="text-sm text-gray-500 mb-4">Try adjusting your filters or search query</p>
              {(searchQuery || difficultyFilter !== 'all' || typeFilter !== 'all') && (
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setDifficultyFilter('all');
                    setTypeFilter('all');
                  }}
                  className="text-sm text-[#00B38F] hover:text-[#009977] font-medium"
                >
                  Clear all filters
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-5 lg:gap-6">
              {filteredCourses.map((course) => (
                <div
                  key={course.id}
                  onClick={() => handleCourseClick(course)}
                  className="group bg-white rounded-xl overflow-hidden hover:shadow-xl transition-all duration-300 cursor-pointer border border-gray-200 hover:border-[#00B38F]/30 flex flex-col"
                >
                  {/* Thumbnail - Fixed Height */}
                  <div className="relative w-full h-48 sm:h-52 bg-gradient-to-br from-gray-100 to-gray-200 flex-shrink-0">
                    {getCourseThumbnail(course) ? (
                      <img 
                        src={getCourseThumbnail(course)!} 
                        alt={course.title} 
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        onError={(e) => {
                          if (course.first_lesson_thumbnail?.medium && e.currentTarget.src !== course.first_lesson_thumbnail.medium) {
                            e.currentTarget.src = course.first_lesson_thumbnail.medium;
                          } else if (course.thumbnail && e.currentTarget.src !== course.thumbnail) {
                            e.currentTarget.src = course.thumbnail;
                          } else {
                            e.currentTarget.style.display = 'none';
                            const placeholder = e.currentTarget.nextElementSibling as HTMLElement;
                            if (placeholder) placeholder.style.display = 'flex';
                          }
                        }}
                      />
                    ) : null}
                    {!getCourseThumbnail(course) && (
                      <div className="w-full h-full flex items-center justify-center">
                        <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                      </div>
                    )}
                    
                    {/* Progress Bar */}
                    {course.is_enrolled && course.progress_percentage > 0 && (
                      <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-black/20 backdrop-blur-sm">
                        <div 
                          className="h-full bg-[#00B38F] transition-all duration-500" 
                          style={{ width: `${course.progress_percentage}%` }} 
                        />
                      </div>
                    )}

                    {/* Badges Row */}
                    <div className="absolute top-3 left-3 right-3 flex items-center justify-between">
                      {/* Type Badge */}
                      <span className={`px-3 py-1.5 rounded-lg text-xs font-semibold shadow-sm ${
                        course.course_type === 'free' 
                          ? 'bg-white/95 text-gray-800 backdrop-blur-sm' 
                          : 'bg-gray-900/90 text-white backdrop-blur-sm'
                      }`}>
                        {course.course_type === 'free' ? 'Free' : 'Premium'}
                      </span>

                      {/* Difficulty Badge */}
                      <span className="px-3 py-1.5 bg-white/95 backdrop-blur-sm text-gray-700 text-xs font-medium rounded-lg shadow-sm capitalize">
                        {course.difficulty_level}
                      </span>
                    </div>
                  </div>

                  {/* Content - Structured Height */}
                  <div className="p-4 sm:p-5 flex flex-col flex-grow">
                    {/* Title - Fixed Height with Clamp */}
                    <h3 className="text-base sm:text-lg font-bold text-gray-900 mb-2 line-clamp-2 group-hover:text-[#00B38F] transition-colors h-12 sm:h-14">
                      {course.title}
                    </h3>

                    {/* Description - Fixed Height with Clamp */}
                    <p className="text-sm text-gray-600 mb-4 line-clamp-2 h-10 sm:h-11">
                      {course.short_description}
                    </p>

                    {/* Footer - Always at Bottom */}
                    <div className="mt-auto pt-4 border-t border-gray-100">
                      {/* Stats Row */}
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3 text-xs text-gray-500">
                          <span className="flex items-center gap-1.5">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {course.estimated_duration}m
                          </span>
                          <span className="flex items-center gap-1.5">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            {course.total_lessons} {course.total_lessons === 1 ? 'lesson' : 'lessons'}
                          </span>
                        </div>
                      </div>

                      {/* Status Button */}
                      {course.is_enrolled ? (
                        <div className="flex items-center gap-2 text-[#00B38F] font-semibold text-sm bg-[#00B38F]/10 px-3 py-2 rounded-lg">
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span>{course.progress_percentage > 0 ? `${course.progress_percentage}% Complete` : 'Enrolled'}</span>
                        </div>
                      ) : course.requires_subscription ? (
                        <div className="flex items-center gap-2 text-gray-700 font-medium text-sm bg-gray-100 px-3 py-2 rounded-lg">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                          </svg>
                          <span>Requires Premium</span>
                        </div>
                      ) : (
                        <div className="flex items-center justify-between text-[#00B38F] font-semibold text-sm group-hover:gap-2 transition-all">
                          <span>Start Learning</span>
                          <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                          </svg>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          </div>
        </div>
      </main>
    </div>
  );
}
