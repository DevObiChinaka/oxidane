'use client';

import React, { useState } from 'react';
import { Course } from '../types/admin';

interface DeleteCourseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  course: Course | null;
  loading?: boolean;
}

export default function DeleteCourseModal({ 
  isOpen, 
  onClose, 
  onConfirm, 
  course, 
  loading = false 
}: DeleteCourseModalProps) {
  const [confirmText, setConfirmText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  const handleConfirm = async () => {
    if (confirmText !== course?.title) {
      return;
    }

    setIsDeleting(true);
    try {
      await onConfirm();
      onClose();
      setConfirmText('');
    } catch (error) {
      console.error('Error deleting course:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleClose = () => {
    if (!isDeleting) {
      setConfirmText('');
      onClose();
    }
  };

  if (!isOpen || !course) return null;

  const canDelete = confirmText === course.title;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
              <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
          </div>
          <div className="mt-3 text-center">
            <h3 className="text-lg font-medium text-gray-900">
              Delete Course
            </h3>
            <div className="mt-2">
              <p className="text-sm text-gray-500">
                This action cannot be undone. This will permanently delete the course and remove all associated data.
              </p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Course Info */}
          <div className="mb-4 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900">{course.title}</h4>
            <div className="mt-2 grid grid-cols-2 gap-4 text-sm text-gray-600">
              <div>
                <span className="font-medium">Status:</span> {course.status}
              </div>
              <div>
                <span className="font-medium">Type:</span> {course.course_type}
              </div>
              <div>
                <span className="font-medium">Lessons:</span> {course.lesson_count || 0}
              </div>
              <div>
                <span className="font-medium">Students:</span> {course.enrollment_count || 0}
              </div>
            </div>
          </div>

          {/* Warning Messages */}
          <div className="mb-4 space-y-2">
            <div className="flex items-start space-x-2 text-sm text-red-600">
              <svg className="h-4 w-4 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <span>All course content and lessons will be permanently deleted</span>
            </div>
            
            {course.enrollment_count && course.enrollment_count > 0 && (
              <div className="flex items-start space-x-2 text-sm text-red-600">
                <svg className="h-4 w-4 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                <span>
                  This course has <strong>{course.enrollment_count} enrolled student{course.enrollment_count !== 1 ? 's' : ''}</strong> who will lose access
                </span>
              </div>
            )}

            <div className="flex items-start space-x-2 text-sm text-red-600">
              <svg className="h-4 w-4 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <span>Student progress and completion data will be lost</span>
            </div>
          </div>

          {/* Confirmation Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Type the course title <strong>"{course.title}"</strong> to confirm deletion:
            </label>
            <input
              type="text"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 transition-all ${
                confirmText && !canDelete 
                  ? 'border-red-300 focus:ring-red-500' 
                  : 'border-gray-300 focus:ring-blue-500'
              }`}
              placeholder="Enter course title to confirm"
              disabled={isDeleting}
            />
            {confirmText && !canDelete && (
              <p className="mt-1 text-sm text-red-600">
                Course title doesn't match. Please type exactly: "{course.title}"
              </p>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={handleClose}
            disabled={isDeleting}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={!canDelete || isDeleting || loading}
            className={`px-6 py-2 rounded-lg font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 transition-all flex items-center ${
              canDelete && !isDeleting
                ? 'bg-red-600 hover:bg-red-700 text-white focus:ring-red-500'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            {isDeleting || loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                Deleting...
              </>
            ) : (
              <>
                <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Delete Course
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}