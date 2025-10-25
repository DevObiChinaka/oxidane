'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import DashboardSidebar from '../components/DashboardSidebar';

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
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        // Not authenticated, redirect to login
        router.push('/auth');
        return;
      }

      // Verify token is valid by checking profile
      const profileResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/profile/`, {
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
      await fetchCourses();
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      router.push('/auth');
    }
  };

  const fetchCourses = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/courses/`, {
        headers
      });

      if (response.ok) {
        const data = await response.json();
        setCourses(data.courses || []);
      } else if (response.status === 401) {
        // Token expired during fetch
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        router.push('/auth');
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

  const handleCourseClick = (course: Course) => {
    router.push(`/courses/${course.slug}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <DashboardSidebar />
        <div className="ml-64 flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#00B38F]"></div>
            <p className="text-slate-300">Loading courses...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <DashboardSidebar />

      {/* Main Content */}
      <main className="ml-64 min-h-screen">
        <header className="bg-slate-800/30 backdrop-blur-sm border-b border-slate-700/50 px-8 py-6">
          <h2 className="text-2xl font-bold text-white">Browse Courses</h2>
          <p className="text-slate-400 mt-1">Expand your forex trading knowledge</p>
        </header>

        <div className="p-8">
          {/* Filters */}
          <div className="mb-8 space-y-4">
            {/* Search */}
            <div className="relative">
              <input
                type="text"
                placeholder="Search courses..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-3 pl-12 bg-slate-800/50 border border-slate-700/50 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00B38F]"
              />
              <svg
                className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 transform -translate-y-1/2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>

            {/* Filter Buttons */}
            <div className="flex flex-wrap gap-4">
              <div className="flex space-x-2">
                <button
                  onClick={() => setDifficultyFilter('all')}
                  className={`px-4 py-2 rounded-lg transition-all ${
                    difficultyFilter === 'all'
                      ? 'bg-[#00B38F] text-white'
                      : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  All Levels
                </button>
                <button
                  onClick={() => setDifficultyFilter('beginner')}
                  className={`px-4 py-2 rounded-lg transition-all ${
                    difficultyFilter === 'beginner'
                      ? 'bg-[#00B38F] text-white'
                      : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  Beginner
                </button>
                <button
                  onClick={() => setDifficultyFilter('intermediate')}
                  className={`px-4 py-2 rounded-lg transition-all ${
                    difficultyFilter === 'intermediate'
                      ? 'bg-[#00B38F] text-white'
                      : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  Intermediate
                </button>
                <button
                  onClick={() => setDifficultyFilter('advanced')}
                  className={`px-4 py-2 rounded-lg transition-all ${
                    difficultyFilter === 'advanced'
                      ? 'bg-[#00B38F] text-white'
                      : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  Advanced
                </button>
              </div>

              <div className="flex space-x-2">
                <button
                  onClick={() => setTypeFilter('all')}
                  className={`px-4 py-2 rounded-lg transition-all ${
                    typeFilter === 'all'
                      ? 'bg-[#00B38F] text-white'
                      : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  All Courses
                </button>
                <button
                  onClick={() => setTypeFilter('free')}
                  className={`px-4 py-2 rounded-lg transition-all ${
                    typeFilter === 'free'
                      ? 'bg-[#00B38F] text-white'
                      : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  Free Only
                </button>
                <button
                  onClick={() => setTypeFilter('premium')}
                  className={`px-4 py-2 rounded-lg transition-all ${
                    typeFilter === 'premium'
                      ? 'bg-[#00B38F] text-white'
                      : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  Premium Only
                </button>
              </div>
            </div>

            <p className="text-slate-400 text-sm">
              Showing {filteredCourses.length} of {courses.length} courses
            </p>
          </div>

          {/* Courses Grid */}
          {filteredCourses.length === 0 ? (
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-12 text-center">
              <svg
                className="w-16 h-16 text-slate-600 mx-auto mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <h3 className="text-xl font-bold text-white mb-2">No courses found</h3>
              <p className="text-slate-400">Try adjusting your filters</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredCourses.map((course) => (
                <div
                  key={course.id}
                  onClick={() => handleCourseClick(course)}
                  className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl overflow-hidden hover:border-[#00B38F]/50 transition-all cursor-pointer group"
                >
                  {/* Course Thumbnail */}
                  <div className="relative h-48 bg-gradient-to-br from-[#00B38F]/20 to-[#000856]/20 flex items-center justify-center">
                    {course.thumbnail ? (
                      <img src={course.thumbnail} alt={course.title} className="w-full h-full object-cover" />
                    ) : (
                      <svg
                        className="w-16 h-16 text-[#00B38F]/50"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                    )}
                    
                    {/* Badges */}
                    <div className="absolute top-4 left-4 right-4 flex justify-between items-start">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        course.course_type === 'free'
                          ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                          : 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                      }`}>
                        {course.course_type === 'free' ? 'Free' : 'Premium'}
                      </span>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getDifficultyColor(course.difficulty_level)}`}>
                        {course.difficulty_level}
                      </span>
                    </div>

                    {/* Progress bar for enrolled courses */}
                    {course.is_enrolled && course.progress_percentage > 0 && (
                      <div className="absolute bottom-0 left-0 right-0 h-2 bg-slate-700/50">
                        <div
                          className="h-full bg-gradient-to-r from-[#00B38F] to-[#00D4A3]"
                          style={{ width: `${course.progress_percentage}%` }}
                        />
                      </div>
                    )}
                  </div>

                  {/* Course Info */}
                  <div className="p-6">
                    <h3 className="text-lg font-bold text-white mb-2 group-hover:text-[#00B38F] transition-colors">
                      {course.title}
                    </h3>
                    <p className="text-sm text-slate-400 mb-4 line-clamp-2">{course.short_description}</p>

                    <div className="flex items-center justify-between text-xs text-slate-500 mb-4">
                      <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {course.estimated_duration} min
                      </span>
                      <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        {course.total_lessons} lessons
                      </span>
                    </div>

                    {/* Status/Action */}
                    {course.is_enrolled ? (
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-green-400 flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          Enrolled
                        </span>
                        {course.progress_percentage > 0 && (
                          <span className="text-xs text-slate-400">
                            {course.progress_percentage}% Complete
                          </span>
                        )}
                      </div>
                    ) : course.requires_subscription ? (
                      <div className="flex items-center text-xs text-purple-400">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                        Requires Mentorship
                      </div>
                    ) : (
                      <div className="text-xs text-slate-400">
                        Click to enroll
                      </div>
                    )}
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
