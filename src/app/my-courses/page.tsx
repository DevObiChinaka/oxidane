'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
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

  useEffect(() => {
    checkAuthAndFetchCourses();
  }, []);

  const checkAuthAndFetchCourses = async () => {
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
      await fetchEnrolledCourses();
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      router.push('/auth');
    }
  };

  const fetchEnrolledCourses = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        router.push('/auth');
        return;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/courses/enrolled/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          router.push('/auth');
          return;
        }
        throw new Error('Failed to fetch courses');
      }

      const data = await response.json();
      console.log('Enrolled courses data:', data);
      console.log('Courses array:', data.courses);
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
        return 'bg-green-500/20 text-green-400';
      case 'intermediate':
        return 'bg-yellow-500/20 text-yellow-400';
      case 'advanced':
        return 'bg-red-500/20 text-red-400';
      default:
        return 'bg-slate-500/20 text-slate-400';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#00B38F]"></div>
          <p className="text-slate-300">Loading courses...</p>
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
          <h2 className="text-2xl font-bold text-white">My Courses</h2>
          <p className="text-slate-400 mt-1">Continue your learning journey</p>
        </header>

        <div className="p-8">
          {/* Filters and Search */}
          <div className="mb-8 flex items-center justify-between">
            <div className="flex space-x-4">
              <button
                onClick={() => setFilter('all')}
                className={`px-6 py-3 rounded-lg font-medium transition-all ${
                  filter === 'all'
                    ? 'bg-[#00B38F] text-white'
                    : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
                }`}
              >
                All Courses ({courses.length})
              </button>
              <button
                onClick={() => setFilter('in-progress')}
                className={`px-6 py-3 rounded-lg font-medium transition-all ${
                  filter === 'in-progress'
                    ? 'bg-[#00B38F] text-white'
                    : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
                }`}
              >
                In Progress ({courses.filter(c => c.progress_percentage > 0 && c.progress_percentage < 100).length})
              </button>
              <button
                onClick={() => setFilter('completed')}
                className={`px-6 py-3 rounded-lg font-medium transition-all ${
                  filter === 'completed'
                    ? 'bg-[#00B38F] text-white'
                    : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
                }`}
              >
                Completed ({courses.filter(c => c.progress_percentage === 100).length})
              </button>
            </div>

            <div className="relative">
              <input
                type="text"
                placeholder="Search courses..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="px-4 py-3 pl-12 bg-slate-800/50 border border-slate-700/50 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00B38F] w-80"
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
              <p className="text-slate-400 mb-6">You haven't enrolled in any courses yet</p>
              <button
                onClick={() => router.push('/courses')}
                className="px-6 py-3 bg-[#00B38F] hover:bg-[#00A87D] text-white rounded-lg transition-all"
              >
                Browse Courses
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredCourses.map((course) => (
                <div
                  key={course.id}
                  className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl overflow-hidden hover:border-[#00B38F]/50 transition-all cursor-pointer group"
                  onClick={() => router.push(`/courses/${course.slug}`)}
                >
                  {/* Course Thumbnail */}
                  <div className="relative h-48 bg-gradient-to-br from-[#00B38F]/20 to-[#000856]/20 flex items-center justify-center">
                    <svg
                      className="w-16 h-16 text-[#00B38F]/50"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                    <span className={`absolute top-4 right-4 px-3 py-1 rounded-full text-sm ${getLevelColor(course.difficulty_level)}`}>
                      {course.difficulty_level}
                    </span>
                  </div>

                  {/* Course Info */}
                  <div className="p-6">
                    <h3 className="text-lg font-bold text-white mb-2 group-hover:text-[#00B38F] transition-colors">
                      {course.title}
                    </h3>
                    <p className="text-sm text-slate-400 mb-4 line-clamp-2">{course.short_description}</p>

                    <div className="flex items-center space-x-4 text-xs text-slate-500 mb-4">
                      <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
                        </svg>
                        {course.total_lessons} lessons
                      </span>
                      <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {course.estimated_duration}
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="mb-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-slate-400">Progress</span>
                        <span className="text-sm font-medium text-[#00B38F]">{course.progress_percentage}%</span>
                      </div>
                      <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-[#00B38F] to-[#00D4A3] rounded-full transition-all"
                          style={{ width: `${course.progress_percentage}%` }}
                        />
                      </div>
                      <p className="text-xs text-slate-500 mt-2">
                        {course.lessons_completed} of {course.total_lessons} lessons completed
                      </p>
                    </div>

                    {/* Action Button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        router.push(`/courses/${course.slug}/watch`);
                      }}
                      className="w-full px-4 py-3 bg-[#00B38F] hover:bg-[#00A87D] text-white rounded-lg transition-all flex items-center justify-center space-x-2"
                    >
                      {course.progress_percentage === 100 ? (
                        <>
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          <span>Review</span>
                        </>
                      ) : (
                        <>
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span>Continue Learning</span>
                        </>
                      )}
                    </button>
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
