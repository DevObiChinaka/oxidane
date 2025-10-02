'use client';

import React, { useState, useEffect } from 'react';
import { Course } from '../types/admin';

interface CourseFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (courseData: Partial<Course>) => Promise<void>;
  course?: Course | null; // null for create, Course object for edit
  loading?: boolean;
}

interface CourseFormData {
  title: string;
  slug: string;
  description: string;
  short_description: string;
  course_type: 'free' | 'premium';
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
  status: 'draft' | 'published' | 'archived';
  meta_title: string;
  meta_description: string;
  keywords: string;
  estimated_duration: number;
  order: number;
}

export default function CourseFormModal({ 
  isOpen, 
  onClose, 
  onSubmit, 
  course, 
  loading = false 
}: CourseFormModalProps) {
  const [formData, setFormData] = useState<CourseFormData>({
    title: '',
    slug: '',
    description: '',
    short_description: '',
    course_type: 'free',
    difficulty_level: 'beginner',
    status: 'draft',
    meta_title: '',
    meta_description: '',
    keywords: '',
    estimated_duration: 0,
    order: 0,
  });

  const [errors, setErrors] = useState<Partial<Record<keyof CourseFormData, string>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Generate slug from title
  const generateSlug = (title: string): string => {
    return title
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9 -]/g, '') // Remove special characters
      .replace(/\s+/g, '-') // Replace spaces with hyphens
      .replace(/-+/g, '-') // Replace multiple hyphens with single hyphen
      .replace(/^-|-$/g, ''); // Remove leading/trailing hyphens
  };

  // Generate SEO suggestions based on course data
  const generateSEOSuggestions = (title: string, difficulty: string, courseType: string) => {
    const difficultyText = difficulty.charAt(0).toUpperCase() + difficulty.slice(1);
    const typeText = courseType === 'premium' ? 'Premium' : 'Free';
    
    const baseSuggestions = {
      meta_title: title ? `${title} - ${difficultyText} ${typeText} Forex Course | OxiWorld Academy` : '',
      meta_description: title ? 
        `Learn ${title.toLowerCase()} with our comprehensive ${difficulty} forex trading course. ${courseType === 'premium' ? 'Premium content with advanced strategies.' : 'Free course for beginners.'} Start trading forex professionally.` : 
        '',
      keywords: [
        'forex trading',
        'currency trading',
        `${difficulty} forex`,
        'forex education',
        'trading strategies',
        'forex academy',
        'trading course',
        'forex learning',
        ...(courseType === 'premium' ? ['premium trading', 'advanced forex'] : ['free forex course', 'forex basics']),
        ...(difficulty === 'beginner' ? ['forex for beginners', 'learn forex'] : 
           difficulty === 'intermediate' ? ['forex strategies', 'trading techniques'] : 
           ['advanced trading', 'professional forex', 'forex mastery'])
      ].join(', ')
    };

    return baseSuggestions;
  };

  // Auto-generate SEO suggestions when title, difficulty, or course type changes
  const handleSEOAutoFill = () => {
    const suggestions = generateSEOSuggestions(formData.title, formData.difficulty_level, formData.course_type);
    setFormData(prev => ({
      ...prev,
      meta_title: suggestions.meta_title,
      meta_description: suggestions.meta_description,
      keywords: suggestions.keywords
    }));
  };

  // Populate form when editing
  useEffect(() => {
    if (course) {
      console.log('🔍 CourseFormModal: Populating form with course data:', {
        course,
        hasMetaTitle: !!course.meta_title,
        hasMetaDescription: !!course.meta_description,
        hasKeywords: !!course.keywords,
        hasDescription: !!course.description
      });
      
      setFormData({
        title: course.title || '',
        slug: course.slug || '',
        description: course.description || '',
        short_description: course.short_description || '',
        course_type: course.course_type || 'free',
        difficulty_level: course.difficulty_level || 'beginner',
        status: course.status || 'draft',
        meta_title: course.meta_title || '',
        meta_description: course.meta_description || '',
        keywords: course.keywords || '',
        estimated_duration: course.estimated_duration || 0,
        order: course.order || 0,
      });
    } else {
      // Reset form for create with default SEO suggestions
      const defaultData = {
        title: '',
        slug: '',
        description: '',
        short_description: '',
        course_type: 'free' as const,
        difficulty_level: 'beginner' as const,
        status: 'draft' as const,
        meta_title: '',
        meta_description: '',
        keywords: 'forex trading, currency trading, forex education, trading strategies, forex academy',
        estimated_duration: 0,
        order: 0,
      };
      setFormData(defaultData);
    }
    setErrors({});
  }, [course, isOpen]);

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof CourseFormData, string>> = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Course title is required';
    } else if (formData.title.length < 3) {
      newErrors.title = 'Title must be at least 3 characters';
    }

    if (!formData.slug.trim()) {
      newErrors.slug = 'Course slug is required';
    } else if (!/^[a-z0-9-]+$/.test(formData.slug)) {
      newErrors.slug = 'Slug can only contain lowercase letters, numbers, and hyphens';
    } else if (formData.slug.length < 3) {
      newErrors.slug = 'Slug must be at least 3 characters';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Course description is required';
    } else if (formData.description.length < 20) {
      newErrors.description = 'Description must be at least 20 characters';
    }

    if (!formData.short_description.trim()) {
      newErrors.short_description = 'Short description is required';
    } else if (formData.short_description.length < 10) {
      newErrors.short_description = 'Short description must be at least 10 characters';
    }

    if (formData.estimated_duration <= 0) {
      newErrors.estimated_duration = 'Estimated duration must be greater than 0';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    console.log('📝 Form submitted with data:', formData);
    console.log('📝 Course being edited:', course?.id);
    
    if (!validateForm()) {
      console.log('❌ Form validation failed');
      return;
    }

    console.log('✅ Form validation passed, submitting...');
    setIsSubmitting(true);
    try {
      await onSubmit(formData);
      console.log('✅ Form submission successful');
      onClose();
    } catch (error) {
      console.error('❌ Error submitting course:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (
    field: keyof CourseFormData,
    value: string | number
  ) => {
    const updates: Partial<CourseFormData> = { [field]: value };
    
    // Auto-generate slug when title changes (only for new courses)
    if (field === 'title' && !course) {
      updates.slug = generateSlug(value as string);
    }
    
    setFormData(prev => ({ ...prev, ...updates }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {course ? 'Edit Course' : 'Create New Course'}
            </h2>
            <p className="text-gray-600 mt-1">
              {course ? 'Update course information and settings' : 'Add a new course to your forex academy'}
            </p>
          </div>
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors disabled:opacity-50"
          >
            <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Basic Information */}
            <div className="lg:col-span-2">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h3>
            </div>

            <div className="lg:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Course Title *
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => handleInputChange('title', e.target.value)}
                className={`w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-black ${
                  errors.title ? 'border-red-300 bg-red-50' : 'border-gray-300 bg-white'
                }`}
                placeholder="Enter course title (e.g., Advanced Forex Trading Strategies)"
                disabled={isSubmitting}
              />
              {errors.title && (
                <p className="mt-1 text-sm text-red-600">{errors.title}</p>
              )}
            </div>

            <div className="lg:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Course Slug *
              </label>
              <input
                type="text"
                value={formData.slug}
                onChange={(e) => handleInputChange('slug', e.target.value)}
                className={`w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-black ${
                  errors.slug ? 'border-red-300 bg-red-50' : 'border-gray-300 bg-white'
                }`}
                placeholder="course-url-slug (auto-generated from title)"
                disabled={isSubmitting}
              />
              {errors.slug && (
                <p className="mt-1 text-sm text-red-600">{errors.slug}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                URL-friendly version of the title. Will be used in course URLs.
              </p>
            </div>

            <div className="lg:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Short Description *
              </label>
              <input
                type="text"
                value={formData.short_description}
                onChange={(e) => handleInputChange('short_description', e.target.value)}
                className={`w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-black ${
                  errors.short_description ? 'border-red-300 bg-red-50' : 'border-gray-300 bg-white'
                }`}
                placeholder="Brief course summary for previews and cards"
                disabled={isSubmitting}
              />
              {errors.short_description && (
                <p className="mt-1 text-sm text-red-600">{errors.short_description}</p>
              )}
            </div>

            <div className="lg:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Full Description *
              </label>
              <textarea
                rows={4}
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                className={`w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-black ${
                  errors.description ? 'border-red-300 bg-red-50' : 'border-gray-300 bg-white'
                }`}
                placeholder="Detailed course description, what students will learn, prerequisites, etc."
                disabled={isSubmitting}
              />
              {errors.description && (
                <p className="mt-1 text-sm text-red-600">{errors.description}</p>
              )}
            </div>

            {/* Course Settings */}
            <div className="lg:col-span-2 pt-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Course Settings</h3>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Course Type
              </label>
              <select
                value={formData.course_type}
                onChange={(e) => handleInputChange('course_type', e.target.value as 'free' | 'premium')}
                className="w-full px-4 py-3 border border-gray-300 bg-white rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
                disabled={isSubmitting}
              >
                <option value="free">Free Course</option>
                <option value="premium">Premium Course</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Difficulty Level
              </label>
              <select
                value={formData.difficulty_level}
                onChange={(e) => handleInputChange('difficulty_level', e.target.value as 'beginner' | 'intermediate' | 'advanced')}
                className="w-full px-4 py-3 border border-gray-300 bg-white rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
                disabled={isSubmitting}
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Publication Status
              </label>
              <select
                value={formData.status}
                onChange={(e) => handleInputChange('status', e.target.value as 'draft' | 'published' | 'archived')}
                className="w-full px-4 py-3 border border-gray-300 bg-white rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
                disabled={isSubmitting}
              >
                <option value="draft">Draft</option>
                <option value="published">Published</option>
                <option value="archived">Archived</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Estimated Duration (minutes) *
              </label>
              <input
                type="number"
                min="1"
                value={formData.estimated_duration}
                onChange={(e) => handleInputChange('estimated_duration', parseInt(e.target.value) || 0)}
                className={`w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-900 ${
                  errors.estimated_duration ? 'border-red-300 bg-red-50' : 'border-gray-300 bg-white'
                }`}
                placeholder="Total course duration in minutes"
                disabled={isSubmitting}
              />
              {errors.estimated_duration && (
                <p className="mt-1 text-sm text-red-600">{errors.estimated_duration}</p>
              )}
            </div>

            {/* SEO Settings */}
            <div className="lg:col-span-2 pt-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">SEO & Metadata</h3>
                <button
                  type="button"
                  onClick={handleSEOAutoFill}
                  disabled={!formData.title.trim()}
                  className="inline-flex items-center px-3 py-2 border border-blue-300 rounded-lg text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Auto-Generate SEO
                </button>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Click "Auto-Generate SEO" to populate fields with forex-optimized suggestions based on your course title and settings.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                SEO Title
              </label>
              <input
                type="text"
                value={formData.meta_title}
                onChange={(e) => handleInputChange('meta_title', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 bg-white rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
                placeholder="SEO optimized title (optional)"
                disabled={isSubmitting}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Display Order
              </label>
              <input
                type="number"
                min="0"
                value={formData.order}
                onChange={(e) => handleInputChange('order', parseInt(e.target.value) || 0)}
                className="w-full px-4 py-3 border border-gray-300 bg-white rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
                placeholder="Course display order"
                disabled={isSubmitting}
              />
            </div>

            <div className="lg:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                SEO Description
              </label>
              <textarea
                rows={2}
                value={formData.meta_description}
                onChange={(e) => handleInputChange('meta_description', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 bg-white rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
                placeholder="SEO meta description (optional)"
                disabled={isSubmitting}
              />
            </div>

            <div className="lg:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Keywords
              </label>
              <input
                type="text"
                value={formData.keywords}
                onChange={(e) => handleInputChange('keywords', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 bg-white rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
                placeholder="Comma-separated keywords (e.g., forex, trading, strategies)"
                disabled={isSubmitting}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-6 mt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-6 py-3 border border-gray-300 rounded-xl text-gray-700 font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || loading}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-medium rounded-xl hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-all flex items-center"
            >
              {isSubmitting || loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                  {course ? 'Updating...' : 'Creating...'}
                </>
              ) : (
                <>
                  <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  {course ? 'Update Course' : 'Create Course'}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
