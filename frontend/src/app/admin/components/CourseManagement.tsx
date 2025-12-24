'use client';

import { useState } from 'react';
import { useCourses, useCourseActions } from '../hooks/useAdminAPI';
import { Course } from '../types/admin';

interface CourseManagementProps {
  className?: string;
}

export default function CourseManagement({ className = '' }: CourseManagementProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [showDropdown, setShowDropdown] = useState<string | null>(null);
  const { data: coursesData, loading, error, refetch } = useCourses(currentPage);
  const { deleteCourse, loading: actionLoading } = useCourseActions();

  const handleDeleteCourse = async (courseId: string) => {
    if (window.confirm('Are you sure you want to delete this course?')) {
      try {
        await deleteCourse(courseId);
        refetch(); // Refresh the courses list
      } catch (error) {
              }
    }
  };

  const getStatusBadge = (status: string) => {
    const statusStyles = {
      published: 'bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium',
      draft: 'bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-xs font-medium',
      archived: 'bg-gray-100 text-gray-800 px-2 py-1 rounded-full text-xs font-medium'
    };
    
    return (
      <span className={statusStyles[status as keyof typeof statusStyles] || statusStyles.draft}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const getTypeBadge = (type: string) => {
    const className = type === 'premium' 
      ? 'bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium'
      : 'bg-gray-100 text-gray-800 px-2 py-1 rounded-full text-xs font-medium';
    
    return (
      <span className={className}>
        {type === 'premium' ? '💎 Premium' : '🆓 Free'}
      </span>
    );
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
        <div className="flex items-center justify-center h-32">
          <div className="flex items-center gap-2">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            <span>Loading courses...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex items-center">
            <div className="text-red-400 mr-2">⚠️</div>
            <div className="text-red-800">
              Error loading courses: {error}
            </div>
          </div>
        </div>
      </div>
    );
  }

  const courses = coursesData?.courses || [];
  const pagination = coursesData?.pagination;

  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Course Management</h2>
            <p className="text-gray-600">Manage your educational content</p>
          </div>
          <button className="bg-[#00B38F] hover:bg-[#00A87D] text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors">
            <span className="text-sm">+</span>
            Add Course
          </button>
        </div>

        {/* Search and Filters */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1">
            <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">🔍</div>
            <input
              type="text"
              placeholder="Search courses..."
              value={searchQuery}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button className="border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 flex items-center gap-2">
            <span>🔽</span>
            Filter
          </button>
        </div>

        {/* Courses Table */}
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Course</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Type</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Status</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Lessons</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Enrolled</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Completion</th>
                <th className="text-right py-3 px-4 font-medium text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {courses.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-8">
                    <div className="flex flex-col items-center gap-2">
                      <div className="text-4xl text-gray-400">📚</div>
                      <p className="text-gray-500">No courses found</p>
                      <button className="border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 text-sm">
                        Create your first course
                      </button>
                    </div>
                  </td>
                </tr>
              ) : (
                courses.map((course) => (
                  <tr key={course.id} className="hover:bg-gray-50">
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-gray-600">
                          ▶️
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{course.title}</p>
                          <p className="text-sm text-gray-500">
                            {course.difficulty_level} • {Math.floor(course.estimated_duration / 60)}h {course.estimated_duration % 60}m
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      {getTypeBadge(course.course_type)}
                    </td>
                    <td className="py-4 px-4">
                      {getStatusBadge(course.status)}
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-1">
                        <span className="text-gray-400">📖</span>
                        {course.lesson_count || 0}
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-1">
                        <span className="text-gray-400">👥</span>
                        {course.enrollment_count || 0}
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-[#00B38F]" 
                            style={{ width: `${course.completion_rate || 0}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-600">
                          {course.completion_rate || 0}%
                        </span>
                      </div>
                    </td>
                    <td className="py-4 px-4 text-right">
                      <div className="relative">
                        <button
                          onClick={() => setShowDropdown(showDropdown === course.id ? null : course.id)}
                          className="p-2 hover:bg-gray-100 rounded-lg"
                        >
                          ⋯
                        </button>
                        {showDropdown === course.id && (
                          <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                            <div className="py-1">
                              <button className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 flex items-center gap-2">
                                👁️ View Details
                              </button>
                              <button className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 flex items-center gap-2">
                                ✏️ Edit Course
                              </button>
                              <button className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 flex items-center gap-2">
                                ▶️ Manage Lessons
                              </button>
                              <button 
                                className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 text-red-600 flex items-center gap-2"
                                onClick={() => {
                                  setShowDropdown(null);
                                  handleDeleteCourse(course.id);
                                }}
                                disabled={actionLoading}
                              >
                                🗑️ Delete Course
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {pagination && pagination.total_pages > 1 && (
          <div className="flex items-center justify-between mt-6">
            <div className="text-sm text-gray-600">
              Showing page {pagination.current_page} of {pagination.total_pages} 
              ({pagination.total_courses} total courses)
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={!pagination.has_previous || loading}
                className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(prev => prev + 1)}
                disabled={!pagination.has_next || loading}
                className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Click outside to close dropdown */}
      {showDropdown && (
        <div 
          className="fixed inset-0 z-0" 
          onClick={() => setShowDropdown(null)}
        />
      )}
    </div>
  );
}