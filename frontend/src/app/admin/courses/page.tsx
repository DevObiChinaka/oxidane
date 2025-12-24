'use client';

import React, { useState } from 'react';
import { useCourses, useCourseActions } from '../hooks/useAdminAPI';
import { adminAPI } from '../utils/api';
import { Course } from '../types/admin';
import CourseFormModal from '../components/CourseFormModal';
import DeleteCourseModal from '../components/DeleteCourseModal';

// Utility function to safely format dates
function formatDate(dateString: string | undefined | null): string {
  if (!dateString || dateString === '' || dateString === 'null' || dateString === 'undefined') {

    return 'No date';
  }
  
  try {
    const date = new Date(dateString);
    // Check if the date is valid
    if (isNaN(date.getTime())) {

      return 'Invalid Date';
    }
    
    // Format the date in a user-friendly way
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  } catch (error) {

    return 'Invalid Date';
  }
}

interface CourseCardProps {
  course: Course;
  onEdit: (course: Course) => void;
  onDelete: (courseId: string) => void;
  onStatusChange: (courseId: string, newStatus: 'draft' | 'published' | 'archived') => Promise<void>;
}

function CourseCard({ course, onEdit, onDelete, onStatusChange }: CourseCardProps) {
  const [showActions, setShowActions] = useState(false);
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);

  const getStatusBadge = (status: string) => {
    const badges = {
      published: 'bg-green-100 text-green-800',
      draft: 'bg-gray-100 text-gray-800',
      archived: 'bg-red-100 text-red-800'
    };
    return badges[status as keyof typeof badges] || badges.draft;
  };

  const getDifficultyBadge = (level: string) => {
    const badges = {
      beginner: 'bg-blue-100 text-blue-800',
      intermediate: 'bg-yellow-100 text-yellow-800',
      advanced: 'bg-red-100 text-red-800'
    };
    return badges[level as keyof typeof badges] || badges.beginner;
  };

  const handleStatusChange = async (newStatus: 'draft' | 'published' | 'archived') => {
    setIsUpdatingStatus(true);
    try {
      await onStatusChange(course.id, newStatus);
    } catch (error) {
          } finally {
      setIsUpdatingStatus(false);
    }
  };

  const getStatusButton = () => {
    if (isUpdatingStatus) {
      return (
        <button 
          disabled
          className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 rounded-md cursor-not-allowed"
        >
          <div className="animate-spin rounded-full h-3 w-3 border-2 border-gray-400 border-t-transparent mr-2"></div>
          Updating...
        </button>
      );
    }

    switch (course.status) {
      case 'draft':
        return (
          <button 
            onClick={() => handleStatusChange('published')}
            className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-green-700 bg-green-50 hover:bg-green-100 border border-green-200 rounded-md transition-colors"
          >
            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Publish
          </button>
        );
      case 'published':
        return (
          <button 
            onClick={() => handleStatusChange('draft')}
            className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-yellow-700 bg-yellow-50 hover:bg-yellow-100 border border-yellow-200 rounded-md transition-colors"
          >
            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
            Unpublish
          </button>
        );
      case 'archived':
        return (
          <button 
            onClick={() => handleStatusChange('draft')}
            className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-md transition-colors"
          >
            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            Restore
          </button>
        );
      default:
        return null;
    }
  };

  return (
    <div 
      className="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className="p-6">
        {/* Header with Status */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(course.status)}`}>
                {course.status.charAt(0).toUpperCase() + course.status.slice(1)}
              </span>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getDifficultyBadge(course.difficulty_level)}`}>
                {course.difficulty_level.charAt(0).toUpperCase() + course.difficulty_level.slice(1)}
              </span>
              {course.course_type === 'premium' && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                  Premium
                </span>
              )}
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">{course.title}</h3>
            <p className="text-sm text-gray-700 line-clamp-2">{course.short_description || course.description}</p>
          </div>
          
          {/* Actions Menu */}
          <div className={`relative transition-opacity duration-200 ${showActions ? 'opacity-100' : 'opacity-0'}`}>
            <button 
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              onClick={() => onEdit(course)}
            >
              <svg className="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-100">
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-900">{course.lesson_count || 0}</div>
            <div className="text-xs text-gray-500">Lessons</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-900">{course.enrollment_count || 0}</div>
            <div className="text-xs text-gray-500">Students</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-900">{course.completion_rate || 0}%</div>
            <div className="text-xs text-gray-500">Completed</div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-4 mt-4 border-t border-gray-100">
          <div className="text-xs text-gray-700">
            Updated {formatDate(course.updated_at)}
          </div>
          <div className="flex items-center gap-2">
            {getStatusButton()}
            <button 
              onClick={() => onEdit(course)}
              className="px-3 py-1 text-xs font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors"
            >
              Edit
            </button>
            <button 
              onClick={() => onDelete(course.id)}
              className="px-3 py-1 text-xs font-medium text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function CoursesPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  
  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);
  
  const { data: coursesData, loading, error, refetch } = useCourses(currentPage, {
    search: searchTerm,
    status: statusFilter
  });

  // Debug: Log courses when data changes
  React.useEffect(() => {
    if (coursesData?.courses) {

    }
  }, [coursesData]);

  const { createCourse, updateCourse, deleteCourse, loading: actionLoading } = useCourseActions();

  const handleEditCourse = async (course: Course) => {

    try {
      // Fetch complete course data with all fields (including SEO fields)

      const completeOneData = await adminAPI.getCourseDetail(course.id);

      setSelectedCourse(completeOneData);
      setShowEditModal(true);
    } catch (error) {
            // Fallback to using list data if detail fetch fails
      setSelectedCourse(course);
      setShowEditModal(true);
    }
  };

  const handleDeleteCourse = (courseId: string) => {
    const course = coursesData?.courses?.find(c => c.id === courseId);
    if (course) {
      setSelectedCourse(course);
      setShowDeleteModal(true);
    }
  };

  const handleCreateCourse = () => {
    setSelectedCourse(null);
    setShowCreateModal(true);
  };

  const handleFormSubmit = async (courseData: Partial<Course>) => {
    try {
      if (selectedCourse) {
        // Edit mode

        const result = await updateCourse(selectedCourse.id, courseData);

        setShowEditModal(false);
      } else {
        // Create mode

        const result = await createCourse(courseData);

        setShowCreateModal(false);
      }
      
      // Refresh the courses list

      await refetch();

    } catch (error) {
            // Error is already handled in the hook and displayed in the modal
    }
  };

  const handleDeleteConfirm = async () => {
    if (!selectedCourse) return;
    
    try {
      await deleteCourse(selectedCourse.id);
      setShowDeleteModal(false);
      setSelectedCourse(null);
      
      // Refresh the courses list
      await refetch();
    } catch (error) {
            // Error is already handled in the hook
    }
  };

  const handleStatusChange = async (courseId: string, newStatus: 'draft' | 'published' | 'archived') => {
    try {
      await updateCourse(courseId, { status: newStatus });
      // Refresh the courses list
      await refetch();
    } catch (error) {
            throw error;
    }
  };

  const handleModalClose = () => {
    setShowCreateModal(false);
    setShowEditModal(false);
    setShowDeleteModal(false);
    setSelectedCourse(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-2 text-gray-700">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
          Loading courses...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-red-500 mb-2">⚠️</div>
          <div className="text-red-600">Error loading courses: {error}</div>
          <button 
            onClick={() => window.location.reload()}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Course Management</h1>
          <p className="text-gray-600">Create and manage your forex academy courses</p>
        </div>
        <button
          onClick={handleCreateCourse}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-200"
        >
          <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Create Course
        </button>
      </div>

      {/* Filters and Search */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <label htmlFor="search" className="block text-sm font-medium text-gray-900 mb-1">
              Search Courses
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-4 w-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                id="search"
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black placeholder-gray-500"
                placeholder="Search by title, description, or keywords..."
              />
            </div>
          </div>
          
          <div className="sm:w-48">
            <label htmlFor="status" className="block text-sm font-medium text-gray-900 mb-1">
              Status Filter
            </label>
            <select
              id="status"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black"
            >
              <option value="">All Statuses</option>
              <option value="published">Published</option>
              <option value="draft">Draft</option>
              <option value="archived">Archived</option>
            </select>
          </div>
        </div>
      </div>

      {/* Course Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <svg className="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-700">Total Courses</p>
              <p className="text-lg font-semibold text-gray-900">{coursesData?.pagination?.total_courses || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <svg className="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-700">Published</p>
              <p className="text-lg font-semibold text-gray-900">
                {coursesData?.courses?.filter(c => c.status === 'published').length || 0}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <svg className="h-5 w-5 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-700">Drafts</p>
              <p className="text-lg font-semibold text-gray-900">
                {coursesData?.courses?.filter(c => c.status === 'draft').length || 0}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <svg className="h-5 w-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-700">Total Students</p>
              <p className="text-lg font-semibold text-gray-900">
            {coursesData?.courses?.reduce((sum, course) => sum + (course.enrollment_count || 0), 0) || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Courses Grid */}
      {coursesData?.courses && coursesData.courses.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {coursesData.courses.map((course) => (
            <CourseCard
              key={course.id}
              course={course}
              onEdit={handleEditCourse}
              onDelete={handleDeleteCourse}
              onStatusChange={handleStatusChange}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No courses found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm || statusFilter ? 'Try adjusting your search criteria.' : 'Get started by creating your first course.'}
          </p>
          <div className="mt-6">
            <button
              onClick={handleCreateCourse}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Create Course
            </button>
          </div>
        </div>
      )}

      {/* Pagination */}
      {coursesData?.pagination && coursesData.pagination.total_pages > 1 && (
        <div className="flex items-center justify-between bg-white px-4 py-3 border border-gray-200 rounded-lg">
          <div className="flex justify-between sm:hidden">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage(Math.min(coursesData.pagination.total_pages, currentPage + 1))}
              disabled={currentPage === coursesData.pagination.total_pages}
              className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
            >
              Next
            </button>
          </div>
          <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Showing <span className="font-medium">{((currentPage - 1) * 10) + 1}</span> to{' '}
                <span className="font-medium">
                  {Math.min(currentPage * 10, coursesData.pagination.total_courses)}
                </span>{' '}
                of <span className="font-medium">{coursesData.pagination.total_courses}</span> courses
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                >
                  Previous
                </button>
                {/* Page numbers could be added here */}
                <button
                  onClick={() => setCurrentPage(Math.min(coursesData.pagination.total_pages, currentPage + 1))}
                  disabled={currentPage === coursesData.pagination.total_pages}
                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                >
                  Next
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}

      {/* Modals */}
      <CourseFormModal
        isOpen={showCreateModal}
        onClose={handleModalClose}
        onSubmit={handleFormSubmit}
        course={null}
        loading={actionLoading}
      />

      <CourseFormModal
        isOpen={showEditModal}
        onClose={handleModalClose}
        onSubmit={handleFormSubmit}
        course={selectedCourse}
        loading={actionLoading}
      />

      <DeleteCourseModal
        isOpen={showDeleteModal}
        onClose={handleModalClose}
        onConfirm={handleDeleteConfirm}
        course={selectedCourse}
        loading={actionLoading}
      />
    </div>
  );
}