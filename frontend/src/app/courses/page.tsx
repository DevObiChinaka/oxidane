'use client';

// Force Vercel rebuild - Courses page redesign deployed 2025-12-18

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
                <p className="text-sm text-gray-600 mt-1 mb-3">Explore our comprehensive collection of forex trading courses</p>
                <div className="flex items-center gap-2">
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
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Search courses..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full px-3 py-2 pl-9 sm:px-4 sm:py-2.5 sm:pl-11 bg-gray-50 border border-gray-200 rounded-full text-sm text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#00B38F] focus:border-transparent transition-all"
                  />
                  <svg 
                    className="w-4 h-4 sm:w-5 sm:h-5 text-gray-400 absolute left-2.5 sm:left-3.5 top-1/2 -translate-y-1/2" 
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

                {/* Filter Pills */}
                <div className="flex gap-2 overflow-x-auto pb-2 hide-scrollbar">
                  <button 
                    onClick={() => setTypeFilter('all')} 
                    className={`px-3 py-1.5 sm:px-4 sm:py-2 rounded-full text-xs sm:text-sm font-medium whitespace-nowrap transition-all ${
                      typeFilter === 'all' 
                        ? 'bg-gray-900 text-white' 
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    All
                  </button>
                  <button 
                    onClick={() => setTypeFilter('free')} 
                    className={`px-3 py-1.5 sm:px-4 sm:py-2 rounded-full text-xs sm:text-sm font-medium whitespace-nowrap transition-all ${
                      typeFilter === 'free' 
                        ? 'bg-gray-900 text-white' 
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    Free
                  </button>
                  <button 
                    onClick={() => setTypeFilter('premium')} 
                    className={`px-3 py-1.5 sm:px-4 sm:py-2 rounded-full text-xs sm:text-sm font-medium whitespace-nowrap transition-all ${
                      typeFilter === 'premium' 
                        ? 'bg-gray-900 text-white' 
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    Premium
                  </button>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Courses Grid */}
        <div className="p-4 sm:p-6 lg:p-8">
          <div className="max-w-[2000px] mx-auto">
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
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4 sm:gap-5 lg:gap-6">
              {filteredCourses.map((course) => (
                <div
                  key={course.id}
                  onClick={() => handleCourseClick(course)}
                  className="group bg-white rounded-xl overflow-hidden hover:shadow-xl transition-all duration-300 cursor-pointer border border-gray-200 hover:border-[#00B38F]/30 flex flex-col"
                >
                  {/* Thumbnail - 16:9 Aspect Ratio */}
                  <div className="relative w-full aspect-video bg-gradient-to-br from-gray-100 to-gray-200 flex-shrink-0">
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

                    {/* Duration Badge */}
                    <div className="absolute bottom-2 right-2">
                      <span className="px-2 py-0.5 bg-black/80 backdrop-blur-sm text-white text-xs font-medium rounded">
                        {course.estimated_duration}m
                      </span>
                    </div>
                    
                    {/* Type Badge */}
                    {course.course_type === 'premium' && (
                      <div className="absolute top-2 left-2">
                        <span className="px-2 py-1 bg-gray-900/90 backdrop-blur-sm text-white text-xs font-semibold rounded">
                          Premium
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Content - Structured Height */}
                  <div className="p-4 flex flex-col flex-grow">
                    {/* Title - Fixed Height with Clamp */}
                    <h3 className="text-sm sm:text-base font-bold text-gray-900 mb-2 line-clamp-2 group-hover:text-[#00B38F] transition-colors min-h-[2.5rem]">
                      {course.title}
                    </h3>

                    {/* Description - Fixed Height with Clamp */}
                    <p className="text-xs sm:text-sm text-gray-600 mb-3 line-clamp-2 min-h-[2.5rem]">
                      {course.short_description}
                    </p>

                    {/* Footer - Always at Bottom */}
                    <div className="mt-auto pt-3 border-t border-gray-100">
                      {/* Metadata Row */}
                      <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
                        <span>{course.total_lessons} {course.total_lessons === 1 ? 'lesson' : 'lessons'}</span>
                        <span>•</span>
                        <span className="capitalize">{course.difficulty_level}</span>
                      </div>

                      {/* Status */}
                      {course.is_enrolled && course.progress_percentage > 0 && (
                        <div className="text-xs text-gray-600">
                          <div className="flex items-center justify-between mb-1">
                            <span>Progress</span>
                            <span className="font-medium">{course.progress_percentage}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-1">
                            <div className="bg-[#00B38F] h-1 rounded-full" style={{ width: `${course.progress_percentage}%` }}></div>
                          </div>
                        </div>
                      )}
                      {course.requires_subscription && !course.is_enrolled && (
                        <div className="text-xs text-gray-600 flex items-center gap-1">
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                          </svg>
                          <span>Premium</span>
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
