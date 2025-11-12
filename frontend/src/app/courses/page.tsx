'use client';

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
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuthAndFetchCourses();
  }, []);

  useEffect(() => {
    filterCourses();
  }, [courses, searchQuery, difficultyFilter, typeFilter]);

  const checkAuthAndFetchCourses = async () => {
    try {
      // Verify token is valid by checking profile
      const profileResponse = await apiGet('/auth/profile/');

      if (!profileResponse.ok) {
        return;
      }

      setIsAuthenticated(true);
      await fetchCourses();
    } catch (error) {
      console.error('Auth check failed:', error);
    }
  };

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

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(course =>
        course.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        course.short_description.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Difficulty filter
    if (difficultyFilter !== 'all') {
      filtered = filtered.filter(course => course.difficulty_level === difficultyFilter);
    }

    // Type filter
    if (typeFilter !== 'all') {
      filtered = filtered.filter(course => course.course_type === typeFilter);
    }

    setFilteredCourses(filtered);
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

  const getDifficultyBadgeColor = (level: string) => {
    switch (level) {
      case 'beginner':
        return 'bg-green-500 text-white';
      case 'intermediate':
        return 'bg-yellow-500 text-white';
      case 'advanced':
        return 'bg-red-500 text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  const getDifficultyColorLight = (level: string) => {
    switch (level) {
      case 'beginner':
        return 'bg-green-100 text-green-700';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-700';
      case 'advanced':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const handleCourseClick = (course: Course) => {
    router.push(`/courses/${course.slug}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <DashboardSidebar />
        <div className="ml-72 flex-1 flex items-center justify-center min-h-screen">
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#00B38F]"></div>
            <p className="text-gray-600">Loading courses...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <DashboardSidebar />

      {/* Main Content */}
      <main className="ml-72 min-h-screen">
        {/* Modern Header with integrated search */}
        <header className="bg-white border-b border-gray-200">
          <div className="px-8 py-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-3xl font-bold text-gray-900">Discover Courses</h2>
                <p className="text-gray-500 text-sm mt-1">Master forex trading with expert-led courses</p>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <span className="text-gray-500">Found</span>
                <span className="px-3 py-1 bg-gray-100 rounded-full font-semibold text-gray-900">{filteredCourses.length}</span>
                <span className="text-gray-500">courses</span>
              </div>
            </div>

            {/* Integrated Search */}
            <div className="relative w-full max-w-xl">
              <input
                type="text"
                placeholder="Search for courses..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-5 py-3.5 pl-12 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#00B38F] focus:border-transparent focus:bg-white transition-all"
              />
              <svg
                className="w-5 h-5 text-gray-400 absolute left-4 top-1/2 transform -translate-y-1/2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>

          {/* Filter Pills - Spaced groups */}
          <div className="px-8 pb-5 flex items-center justify-between gap-6">
            {/* Difficulty Pills - Left */}
            <div className="flex gap-2">
              <button
                onClick={() => setDifficultyFilter('all')}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                  difficultyFilter === 'all'
                    ? 'bg-[#00B38F] text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                All Levels
              </button>
              <button
                onClick={() => setDifficultyFilter('beginner')}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                  difficultyFilter === 'beginner'
                    ? 'bg-[#00B38F] text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                Beginner
              </button>
              <button
                onClick={() => setDifficultyFilter('intermediate')}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                  difficultyFilter === 'intermediate'
                    ? 'bg-[#00B38F] text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                Intermediate
              </button>
              <button
                onClick={() => setDifficultyFilter('advanced')}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                  difficultyFilter === 'advanced'
                    ? 'bg-[#00B38F] text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                Advanced
              </button>
            </div>

            {/* Type Pills - Right */}
            <div className="flex gap-2">
              <button
                onClick={() => setTypeFilter('all')}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                  typeFilter === 'all'
                    ? 'bg-[#00B38F] text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                All Courses
              </button>
              <button
                onClick={() => setTypeFilter('free')}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                  typeFilter === 'free'
                    ? 'bg-[#00B38F] text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                Free
              </button>
              <button
                onClick={() => setTypeFilter('premium')}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                  typeFilter === 'premium'
                    ? 'bg-[#00B38F] text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                Premium
              </button>
            </div>
          </div>
        </header>

        <div className="p-8 max-w-7xl">
          {/* Courses Grid */}
          {filteredCourses.length === 0 ? (
            <div className="bg-white border border-gray-200 rounded-2xl p-16 text-center">
              <div className="w-24 h-24 rounded-full bg-gray-50 flex items-center justify-center mx-auto mb-5">
                <svg
                  className="w-12 h-12 text-[#000856]"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No courses found</h3>
              <p className="text-gray-500">Try adjusting your filters or search query</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
              {filteredCourses.map((course) => (
                <div
                  key={course.id}
                  onClick={() => handleCourseClick(course)}
                  className="group bg-white rounded-lg overflow-hidden hover:shadow-md transition-all cursor-pointer border border-gray-200"
                >
                  {/* Horizontal Layout for Course Card */}
                  <div className="flex flex-col sm:flex-row">
                    {/* Left: Thumbnail/Icon */}
                    <div className="relative w-full sm:w-32 h-32 sm:h-auto bg-gray-50 flex items-center justify-center flex-shrink-0">
                      {course.thumbnail ? (
                        <img src={course.thumbnail} alt={course.title} className="w-full h-full object-cover" />
                      ) : (
                        <svg
                          className="w-12 h-12 text-[#000856]"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                          strokeWidth={1.5}
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                      )}
                      
                      {/* Progress bar */}
                      {course.is_enrolled && course.progress_percentage > 0 && (
                        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200">
                          <div
                            className="h-full bg-[#00B38F]"
                            style={{ width: `${course.progress_percentage}%` }}
                          />
                        </div>
                      )}
                    </div>

                    {/* Right: Content */}
                    <div className="flex-1 p-4">
                      {/* Badges Row */}
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                          course.course_type === 'free'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-purple-100 text-purple-700'
                        }`}>
                          {course.course_type === 'free' ? 'Free' : 'Premium'}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getDifficultyColorLight(course.difficulty_level)}`}>
                          {course.difficulty_level}
                        </span>
                      </div>

                      {/* Title */}
                      <h3 className="text-base font-semibold text-gray-900 mb-1.5 line-clamp-2 group-hover:text-[#00B38F] transition-colors">
                        {course.title}
                      </h3>

                      {/* Description */}
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">{course.short_description}</p>

                      {/* Stats & Status Row */}
                      <div className="flex items-center justify-between text-xs">
                        {/* Stats */}
                        <div className="flex items-center gap-3 text-gray-500">
                          <span className="flex items-center gap-1">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {course.estimated_duration}min
                          </span>
                          <span className="flex items-center gap-1">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            {course.total_lessons}
                          </span>
                        </div>

                        {/* Status */}
                        {course.is_enrolled ? (
                          <div className="flex items-center gap-1.5 text-[#00B38F] font-medium">
                            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {course.progress_percentage > 0 ? `${course.progress_percentage}%` : 'Enrolled'}
                          </div>
                        ) : course.requires_subscription ? (
                          <span className="text-purple-600 font-medium flex items-center gap-1">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                            </svg>
                            Premium
                          </span>
                        ) : (
                          <span className="text-[#00B38F] font-medium">Click to enroll →</span>
                        )}
                      </div>
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
