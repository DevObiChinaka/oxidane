'use client';

import { useState, useEffect } from 'react';
import { useAdminAuth } from '../contexts/AdminAuthContext';
import LessonFormModal from '../components/LessonFormModal';
import DeleteConfirmationModal from '../components/DeleteConfirmationModal';
import { adminAPI } from '../utils/api';
import { useCourses } from '../hooks/useAdminAPI';
import { Lesson, Course } from '../types/admin';

export default function LessonsPage() {
  const { user } = useAdminAuth();
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showLessonModal, setShowLessonModal] = useState(false);
  const [selectedLesson, setSelectedLesson] = useState<Lesson | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCourse, setSelectedCourse] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'title' | 'course' | 'order' | 'created_at'>('order');
  // Per-course pagination state - track current page for each course
  const [coursePagination, setCoursePagination] = useState<{[courseId: string]: number}>({});
  const lessonsPerCourse = 5; // Show 5 lessons per course
  
  // Delete confirmation modal state
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [lessonToDelete, setLessonToDelete] = useState<Lesson | null>(null);

  // Fetch courses using the hook (get first page to have courses available for dropdown)
  const { data: coursesData, loading: coursesLoading, error: coursesError } = useCourses(1, {});

  // Extract courses array from the hook data
  const courses: Course[] = coursesData?.courses || [];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('🔍 Fetching lessons data...');
      
      // Fetch lessons
      try {
        const lessonsResponse = await adminAPI.getAllLessons();
        console.log('🎥 Lessons response:', lessonsResponse);
        
        // Ensure lessons is always an array
        let lessonsArray = [];
        if (Array.isArray(lessonsResponse)) {
          lessonsArray = lessonsResponse;
        } else if (lessonsResponse && Array.isArray(lessonsResponse.results)) {
          lessonsArray = lessonsResponse.results;
        } else if (lessonsResponse && lessonsResponse.data && Array.isArray(lessonsResponse.data)) {
          lessonsArray = lessonsResponse.data;
        }
        console.log('🎥 Processed lessons array:', lessonsArray);
        setLessons(lessonsArray);
      } catch (lessonsError) {
        console.warn('⚠️ Failed to fetch lessons:', lessonsError);
        setLessons([]);
        setError('Failed to load lessons. Please check your connection and try again.');
      }
      
    } catch (err) {
      console.error('❌ Failed to fetch lessons data:', err);
      setError('Failed to load lessons. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateLesson = () => {
    console.log('🎬 Creating lesson, available courses:', Array.isArray(courses) ? courses.length : 0);
    setSelectedLesson(null);
    setShowLessonModal(true);
  };

  const handleEditLesson = (lesson: Lesson) => {
    setSelectedLesson(lesson);
    setShowLessonModal(true);
  };

  const handleDeleteLesson = (lesson: Lesson) => {
    console.log('🗑️ Delete button clicked for lesson:', lesson.title);
    console.log('🗑️ Setting lessonToDelete and showDeleteModal to true');
    setLessonToDelete(lesson);
    setShowDeleteModal(true);
    console.log('🗑️ Modal state should now be open');
  };

  const confirmDeleteLesson = async () => {
    if (!lessonToDelete) return;

    try {
      console.log('🗑️ Deleting lesson:', lessonToDelete.id);
      await adminAPI.deleteLesson(lessonToDelete.id);
      console.log('✅ Lesson deleted successfully');
      
      // Immediately update the local state to remove the deleted lesson
      setLessons(prevLessons => prevLessons.filter(lesson => lesson.id !== lessonToDelete.id));
      
      // Also refresh from server to ensure consistency
      await fetchData();
      
      console.log('🔄 Lessons list updated');
    } catch (error) {
      console.error('❌ Failed to delete lesson:', error);
      throw error; // Let the modal handle the error
    } finally {
      setLessonToDelete(null);
    }
  };

  const handleLessonSaved = async () => {
    console.log('✅ Lesson saved, refreshing data...');
    setShowLessonModal(false);
    setSelectedLesson(null);
    await fetchData(); // Refresh the list
  };

  // Group lessons by course and apply filtering with per-course pagination
  const groupedLessons = () => {
    // Filter lessons first
    const filteredLessons = lessons.filter(lesson => {
      const matchesSearch = lesson.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           lesson.description.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCourse = selectedCourse === 'all' || lesson.course === selectedCourse;
      return matchesSearch && matchesCourse;
    });

    // Group by course with pagination per course
    const grouped = courses.reduce((acc: any, course) => {
      const courseLessons = filteredLessons
        .filter(lesson => lesson.course === course.id)
        .sort((a, b) => {
          switch (sortBy) {
            case 'title':
              return a.title.localeCompare(b.title);
            case 'order':
              return a.order - b.order;
            case 'created_at':
              return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
            default:
              return a.order - b.order;
          }
        });

      if (courseLessons.length > 0) {
        // Get current page for this course (default to 1)
        const currentPage = coursePagination[course.id] || 1;
        const startIndex = (currentPage - 1) * lessonsPerCourse;
        const endIndex = startIndex + lessonsPerCourse;
        
        acc[course.id] = {
          course: course,
          allLessons: courseLessons, // Keep all lessons for stats
          paginatedLessons: courseLessons.slice(startIndex, endIndex), // Current page lessons
          totalLessons: courseLessons.length,
          totalPages: Math.ceil(courseLessons.length / lessonsPerCourse),
          currentPage: currentPage
        };
      }
      return acc;
    }, {});

    return grouped;
  };

  const lessonsGrouped = groupedLessons();
  const courseIds = Object.keys(lessonsGrouped);
  
  // Helper function to handle per-course pagination
  const handleCoursePageChange = (courseId: string, newPage: number) => {
    setCoursePagination(prev => ({
      ...prev,
      [courseId]: newPage
    }));
  };
  
  // Stats calculations
  const totalCourses = courseIds.length;
  const totalLessonsCount = lessons.length;

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  const getVideoSourceIcon = (source: string) => {
    switch (source) {
      case 'youtube':
        return '📺';
      case 'vimeo':
        return '🎬';
      case 'upload':
        return '📁';
      default:
        return '🎥';
    }
  };

  const getCourseTitle = (courseId: string) => {
    if (!Array.isArray(courses)) return 'Unknown Course';
    const course = courses.find(c => c.id === courseId);
    return course?.title || 'Unknown Course';
  };

  if (!user) {
    return <div>Access Denied</div>;
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Lesson Management</h1>
        <p className="text-gray-700">Create and manage your forex academy lessons</p>
      </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            {/* Search and Filters */}
            <div className="flex flex-col sm:flex-row gap-4 flex-1">
              {/* Search */}
              <div className="relative flex-1">
                <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-900">🔍</div>
                <input
                  type="text"
                  placeholder="Search lessons by title or description..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black"
                />
              </div>

              {/* Course Filter */}
              <select
                value={selectedCourse}
                onChange={(e) => setSelectedCourse(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black"
              >
                <option value="all">All Courses</option>
                {Array.isArray(courses) && courses.map(course => (
                  <option key={course.id} value={course.id}>
                    {course.title}
                  </option>
                ))}
              </select>

              {/* Sort */}
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black"
              >
                <option value="order">Sort by Order</option>
                <option value="title">Sort by Title</option>
                <option value="course">Sort by Course</option>
                <option value="created_at">Sort by Date</option>
              </select>
            </div>

            {/* Add Lesson Button */}
            <button
              onClick={handleCreateLesson}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Lesson
            </button>
          </div>
        </div>

        {/* Loading State */}
        {(loading || coursesLoading) && (
          <div className="flex items-center justify-center h-64">
            <div className="flex items-center gap-2 text-gray-700">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
              Loading {loading ? 'lessons' : 'courses'}...
            </div>
          </div>
        )}

        {/* Error State */}
        {(error || coursesError) && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error || coursesError}
          </div>
        )}

        {/* Stats Cards */}
        {!loading && !coursesLoading && !error && !coursesError && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg shadow-sm border">
              <div className="text-2xl font-semibold text-gray-900">{totalCourses}</div>
              <div className="text-sm text-gray-700">Courses with Lessons</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm border">
              <div className="text-2xl font-semibold text-gray-900">
                {Object.values(lessonsGrouped).reduce((sum: number, group: any) => sum + group.allLessons.length, 0)}
              </div>
              <div className="text-sm text-gray-700">Total Lessons</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm border">
              <div className="text-2xl font-semibold text-gray-900">
                {Object.values(lessonsGrouped).reduce((sum: number, group: any) => 
                  sum + group.allLessons.filter((l: any) => l.is_preview).length, 0)}
              </div>
              <div className="text-sm text-gray-700">Preview Lessons</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm border">
              <div className="text-2xl font-semibold text-gray-900">
                {Object.values(lessonsGrouped).reduce((sum: number, group: any) => 
                  sum + group.allLessons.reduce((courseSum: number, l: any) => courseSum + l.duration, 0), 0)}
              </div>
              <div className="text-sm text-gray-700">Total Minutes</div>
            </div>
          </div>
        )}

        {/* Lessons List */}
        {!loading && !coursesLoading && !error && !coursesError && (
          <div className="bg-white rounded-lg shadow-sm border">
            {totalLessonsCount === 0 ? (
              <div className="p-12 text-center">
                <div className="text-4xl text-gray-900 mb-4">📚</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No lessons found</h3>
                <p className="text-gray-700 mb-4">
                  {searchTerm || selectedCourse !== 'all' 
                    ? 'Try adjusting your search or filter criteria.'
                    : (!Array.isArray(courses) || courses.length === 0)
                      ? 'You need to create a course first before adding lessons.'
                      : 'Get started by creating your first lesson.'
                  }
                </p>
                {(!searchTerm && selectedCourse === 'all') && (
                  <>
                    {(!Array.isArray(courses) || courses.length === 0) ? (
                      <button
                        onClick={() => window.location.href = '/admin/courses'}
                        className="bg-[#00B38F] hover:bg-[#00A87D] text-white px-6 py-3 rounded-lg font-medium transition-colors mr-3"
                      >
                        Create Your First Course
                      </button>
                    ) : (
                      <button
                        onClick={handleCreateLesson}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                      >
                        Create First Lesson
                      </button>
                    )}
                  </>
                )}
              </div>
            ) : (
              <div className="space-y-2">
                {/* Course-grouped lessons with per-course pagination */}
                {courseIds.map(courseId => {
                  const courseData = lessonsGrouped[courseId];
                  if (!courseData) return null;
                  
                  const { course, paginatedLessons, totalLessons, totalPages, currentPage } = courseData;
                  
                  return (
                    <div key={courseId} className="bg-white border border-gray-100 rounded-sm overflow-hidden mb-4">
                      {/* Course Header */}
                      <div className="bg-gray-50 px-4 py-2 border-b border-gray-100">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="text-sm font-medium text-gray-700">
                              {course?.title || `Course ${courseId}`}
                            </h3>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="text-xs text-gray-400">
                              {totalLessons} lesson{totalLessons !== 1 ? 's' : ''} total
                            </div>
                            {totalPages > 1 && (
                              <div className="text-xs text-gray-400">
                                Page {currentPage} of {totalPages}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Lessons Table */}
                      <div className="overflow-hidden">
                        {/* Table Header */}
                        <div className="bg-white px-4 py-2 border-b border-gray-100">
                          <div className="grid grid-cols-11 gap-3 text-xs font-medium text-gray-500 uppercase tracking-wide">
                            <div className="col-span-1">Order</div>
                            <div className="col-span-4">Lesson</div>
                            <div className="col-span-1">Duration</div>
                            <div className="col-span-1">Type</div>
                            <div className="col-span-2">Preview</div>
                            <div className="col-span-2">Actions</div>
                          </div>
                        </div>

                        {/* Table Body */}
                        <div className="divide-y divide-gray-100">
                          {paginatedLessons.map((lesson: Lesson) => (
                            <div key={lesson.id} className="px-4 py-3 hover:bg-gray-25 transition-colors">
                              <div className="grid grid-cols-11 gap-3 items-center">
                                {/* Order */}
                                <div className="col-span-1">
                                  <span className="text-xs text-gray-500 font-mono">
                                    #{lesson.order}
                                  </span>
                                </div>

                                {/* Lesson Info */}
                                <div className="col-span-4">
                                  <div className="text-sm font-medium text-gray-900">{lesson.title}</div>
                                  <div className="text-xs text-gray-500 truncate">{lesson.description}</div>
                                </div>

                                {/* Duration */}
                                <div className="col-span-1">
                                  <span className="text-xs text-gray-600">{formatDuration(lesson.duration)}</span>
                                </div>

                                {/* Video Type */}
                                <div className="col-span-1">
                                  <span title={lesson.video_source} className="text-lg">
                                    {getVideoSourceIcon(lesson.video_source)}
                                  </span>
                                </div>

                                {/* Preview Badge */}
                                <div className="col-span-2">
                                  {lesson.is_preview && (
                                    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-green-50 text-green-700">
                                      Preview
                                    </span>
                                  )}
                                </div>

                                {/* Actions */}
                                <div className="col-span-2 flex items-center gap-1">
                                  <button
                                    onClick={() => handleEditLesson(lesson)}
                                    className="text-gray-400 hover:text-blue-600 p-1 transition-colors"
                                    title="Edit lesson"
                                  >
                                    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                    </svg>
                                  </button>
                                  <button
                                    onClick={() => handleDeleteLesson(lesson)}
                                    className="text-gray-400 hover:text-red-600 p-1 transition-colors"
                                    title="Delete lesson"
                                  >
                                    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                    </svg>
                                  </button>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                        
                        {/* Per-Course Pagination */}
                        {totalPages > 1 && (
                          <div className="flex items-center justify-center py-3 border-t border-gray-100">
                            <div className="flex items-center gap-3 text-sm text-gray-500">
                              {/* Previous Button */}
                              <button
                                onClick={() => handleCoursePageChange(courseId, Math.max(currentPage - 1, 1))}
                                disabled={currentPage === 1}
                                className="flex items-center gap-1 text-gray-400 hover:text-gray-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                              >
                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                                </svg>
                                <span className="text-xs">Previous</span>
                              </button>

                              {/* Page Info */}
                              <span className="text-xs text-gray-400 px-2">
                                {currentPage} of {totalPages}
                              </span>

                              {/* Next Button */}
                              <button
                                onClick={() => handleCoursePageChange(courseId, Math.min(currentPage + 1, totalPages))}
                                disabled={currentPage === totalPages}
                                className="flex items-center gap-1 text-gray-400 hover:text-gray-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                              >
                                <span className="text-xs">Next</span>
                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                </svg>
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}

              </div>
            )}
          </div>
        )}

      {/* Lesson Form Modal */}
      {showLessonModal && (
        <LessonFormModal
          lesson={selectedLesson}
          courses={courses}
          onClose={() => setShowLessonModal(false)}
          onSave={handleLessonSaved}
        />
      )}

      {/* Delete Confirmation Modal */}
      <DeleteConfirmationModal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false);
          setLessonToDelete(null);
        }}
        onConfirm={confirmDeleteLesson}
        title="Delete Lesson"
        message="Are you sure you want to delete this lesson? This will permanently remove the lesson and all its associated content."
        itemName={lessonToDelete?.title}
        itemType="lesson"
      />

    </div>
  );
}