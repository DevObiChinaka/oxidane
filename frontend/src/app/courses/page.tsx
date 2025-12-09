'use client';

// Force Vercel rebuild - YouTube thumbnails deployed 2025-12-09

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
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
      <main className="flex-1 min-h-screen w-full overflow-x-hidden lg:ml-0">
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

        {/* Header */}
        <header className="bg-white border-b border-gray-200">
          <div className="px-4 sm:px-6 lg:px-8 py-5 lg:py-6">
            <div className="max-w-7xl mx-auto">
            {/* Title Section */}
            <div className="ml-12 lg:ml-0 mb-5">
              <h2 className="text-2xl lg:text-3xl font-bold text-gray-900">Discover Courses</h2>
              <div className="flex items-center gap-2 mt-2 text-sm">
                <span className="text-gray-500">Found</span>
                <span className="px-2.5 py-0.5 bg-gray-100 rounded-full font-semibold text-gray-900">{filteredCourses.length}</span>
                <span className="text-gray-500">courses</span>
              </div>
            </div>

            {/* Search Bar */}
            <div className="ml-12 lg:ml-0 mb-4">
              <div className="relative max-w-2xl">
                <input
                  type="text"
                  placeholder="Search courses..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-2.5 pl-10 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#00B38F] focus:border-transparent"
                />
                <svg className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>

            {/* Filters */}
            <div className="space-y-3 ml-12 lg:ml-0">
              {/* Difficulty Filter */}
              <div className="flex gap-2 overflow-x-auto pb-2 hide-scrollbar">
                <button onClick={() => setDifficultyFilter('all')} className={`px-3.5 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${difficultyFilter === 'all' ? 'bg-[#00B38F] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                  All Levels
                </button>
                <button onClick={() => setDifficultyFilter('beginner')} className={`px-3.5 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${difficultyFilter === 'beginner' ? 'bg-[#00B38F] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                  Beginner
                </button>
                <button onClick={() => setDifficultyFilter('intermediate')} className={`px-3.5 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${difficultyFilter === 'intermediate' ? 'bg-[#00B38F] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                  Intermediate
                </button>
                <button onClick={() => setDifficultyFilter('advanced')} className={`px-3.5 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${difficultyFilter === 'advanced' ? 'bg-[#00B38F] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                  Advanced
                </button>
              </div>

              {/* Type Filter */}
              <div className="flex gap-2 overflow-x-auto pb-2 hide-scrollbar">
                <button onClick={() => setTypeFilter('all')} className={`px-3.5 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${typeFilter === 'all' ? 'bg-[#00B38F] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                  All Courses
                </button>
                <button onClick={() => setTypeFilter('free')} className={`px-3.5 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${typeFilter === 'free' ? 'bg-[#00B38F] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                  Free
                </button>
                <button onClick={() => setTypeFilter('premium')} className={`px-3.5 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${typeFilter === 'premium' ? 'bg-[#00B38F] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                  Premium
                </button>
              </div>
            </div>
            </div>
          </div>
        </header>

        {/* Courses Grid */}
        <div className="p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">
          {filteredCourses.length === 0 ? (
            <div className="max-w-md mx-auto bg-white border border-gray-200 rounded-lg p-12 text-center">
              <div className="w-20 h-20 rounded-full bg-gray-50 flex items-center justify-center mx-auto mb-4">
                <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No courses found</h3>
              <p className="text-sm text-gray-500">Try adjusting your filters or search query</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-5">
              {filteredCourses.map((course) => (
                <div
                  key={course.id}
                  onClick={() => handleCourseClick(course)}
                  className="group bg-white rounded-lg overflow-hidden hover:shadow-lg transition-shadow cursor-pointer border border-gray-200"
                >
                  {/* Thumbnail */}
                  <div className="relative w-full h-44 bg-gray-100 flex-shrink-0">
                    {getCourseThumbnail(course) ? (
                      <img 
                        src={getCourseThumbnail(course)!} 
                        alt={course.title} 
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          // Fallback to medium quality if maxresdefault doesn't exist
                          if (course.first_lesson_thumbnail?.medium && e.currentTarget.src !== course.first_lesson_thumbnail.medium) {
                            e.currentTarget.src = course.first_lesson_thumbnail.medium;
                          } else if (course.thumbnail && e.currentTarget.src !== course.thumbnail) {
                            e.currentTarget.src = course.thumbnail;
                          } else {
                            // Show placeholder on final failure
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
                      <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-gray-200">
                        <div className="h-full bg-[#00B38F]" style={{ width: `${course.progress_percentage}%` }} />
                      </div>
                    )}

                    {/* Type Badge */}
                    <div className="absolute top-3 left-3">
                      <span className={`px-2.5 py-1 rounded text-xs font-medium ${course.course_type === 'free' ? 'bg-white/90 text-gray-700' : 'bg-gray-900/90 text-white'}`}>
                        {course.course_type === 'free' ? 'Free' : 'Premium'}
                      </span>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="p-5">
                    {/* Difficulty Badge */}
                    <div className="mb-2">
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded border border-gray-200 capitalize">
                        {course.difficulty_level}
                      </span>
                    </div>

                    {/* Title */}
                    <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2 group-hover:text-[#00B38F] transition-colors min-h-[3.5rem]">
                      {course.title}
                    </h3>

                    {/* Description */}
                    <p className="text-sm text-gray-600 mb-4 line-clamp-2 min-h-[2.5rem]">{course.short_description}</p>

                    {/* Footer */}
                    <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                      {/* Stats */}
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          {course.estimated_duration}m
                        </span>
                        <span className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          {course.total_lessons}
                        </span>
                      </div>

                      {/* Status */}
                      {course.is_enrolled ? (
                        <div className="flex items-center gap-1.5 text-[#00B38F] font-medium text-xs">
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span>{course.progress_percentage > 0 ? `${course.progress_percentage}%` : 'Enrolled'}</span>
                        </div>
                      ) : course.requires_subscription ? (
                        <span className="text-gray-600 font-medium flex items-center gap-1 text-xs">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                          </svg>
                          Premium
                        </span>
                      ) : (
                        <span className="text-[#00B38F] font-medium text-xs">Enroll →</span>
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
