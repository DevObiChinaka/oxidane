'use client';

import { useState, useEffect } from 'react';
import { Lesson, Course } from '../types/admin';
import { adminAPI } from '../utils/api';

interface LessonFormModalProps {
  lesson?: Lesson | null;
  courses: Course[];
  onClose: () => void;
  onSave: () => void;
}

export default function LessonFormModal({ lesson, courses, onClose, onSave }: LessonFormModalProps) {
  const [formData, setFormData] = useState({
    title: '',
    slug: '',
    description: '',
    course: '',
    video_source: 'upload' as 'upload' | 'youtube' | 'vimeo',
    video_url: '',
    duration: 0,
    order: 1,
    is_preview: false,
    lesson_notes: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

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

  useEffect(() => {
    if (lesson) {
      setFormData({
        title: lesson.title,
        slug: lesson.slug || '',
        description: lesson.description,
        course: lesson.course,
        video_source: lesson.video_source,
        video_url: lesson.video_url || '',
        duration: lesson.duration,
        order: lesson.order,
        is_preview: lesson.is_preview,
        lesson_notes: lesson.lesson_notes || '',
      });
    } else {
      // Set default course if only one exists
      if (Array.isArray(courses) && courses.length === 1) {
        setFormData(prev => ({ ...prev, course: courses[0].id }));
      }
    }
  }, [lesson, courses]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Basic validation
      if (!formData.title.trim()) {
        throw new Error('Lesson title is required');
      }
      if (!formData.slug.trim()) {
        throw new Error('Lesson slug is required');
      }
      if (!/^[a-z0-9-]+$/.test(formData.slug)) {
        throw new Error('Slug can only contain lowercase letters, numbers, and hyphens');
      }
      if (!formData.course) {
        throw new Error('Please select a course');
      }
      if (!Array.isArray(courses) || courses.length === 0) {
        throw new Error('No courses available. Please create a course first.');
      }
      if (formData.video_source === 'upload' && !selectedFile && !lesson) {
        throw new Error('Please upload a video file');
      }
      if (formData.video_source !== 'upload' && !formData.video_url.trim()) {
        throw new Error('Video URL is required for YouTube/Vimeo videos');
      }

      let response;
      
      if (formData.video_source === 'upload' && selectedFile) {
        // Prepare form data for file upload
        const uploadFormData = new FormData();
        uploadFormData.append('title', formData.title.trim());
        uploadFormData.append('slug', formData.slug.trim());
        uploadFormData.append('description', formData.description.trim());
        uploadFormData.append('course', formData.course);
        uploadFormData.append('video_source', formData.video_source);
        uploadFormData.append('duration', formData.duration.toString());
        uploadFormData.append('order', formData.order.toString());
        uploadFormData.append('is_preview', formData.is_preview.toString());
        uploadFormData.append('lesson_notes', formData.lesson_notes.trim());
        uploadFormData.append('video_file', selectedFile);

        if (lesson) {
          // Update existing lesson with file
          response = await adminAPI.updateLessonWithFile(lesson.id, uploadFormData);
        } else {
          // Create new lesson with file
          response = await adminAPI.createLessonWithFile(formData.course, uploadFormData);
        }
        
              } else {
        // Prepare regular lesson data (no file)
        const lessonData = {
          title: formData.title.trim(),
          slug: formData.slug.trim(),
          description: formData.description.trim(),
          course: formData.course,
          video_source: formData.video_source,
          video_url: formData.video_url.trim(),
          duration: formData.duration,
          order: formData.order,
          is_preview: formData.is_preview,
          lesson_notes: formData.lesson_notes.trim(),
        };

                if (lesson) {
          // Update existing lesson
          response = await adminAPI.updateLesson(lesson.id, lessonData);
                  } else {
          // Create new lesson
          response = await adminAPI.createLesson(formData.course, lessonData);
                  }
      }

      onSave();
    } catch (err: any) {
            setError(err.message || 'Failed to save lesson. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    const updates: any = { [field]: value };
    
    // Auto-generate slug when title changes (only for new lessons)
    if (field === 'title' && !lesson) {
      updates.slug = generateSlug(value as string);
    }
    
    setFormData(prev => ({ ...prev, ...updates }));
  };

  const extractYouTubeId = (url: string) => {
    const regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[7].length === 11) ? match[7] : null;
  };

  // File upload handlers
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleFile = (file: File) => {
    // Validate file type
    const allowedTypes = ['video/mp4', 'video/mov', 'video/quicktime', 'video/x-msvideo'];
    if (!allowedTypes.includes(file.type)) {
      setError('Please select a valid video file (MP4, MOV, or AVI)');
      return;
    }

    // Validate file size (500MB = 500 * 1024 * 1024 bytes)
    const maxSize = 500 * 1024 * 1024;
    if (file.size > maxSize) {
      setError('File size must be less than 500MB');
      return;
    }

    setSelectedFile(file);
    setError(null);

    // Extract duration and convert from seconds to minutes
    const video = document.createElement('video');
    video.preload = 'metadata';
    video.onloadedmetadata = () => {
      window.URL.revokeObjectURL(video.src);
      if (video.duration && !isNaN(video.duration)) {
        // Convert seconds to minutes and round
        const durationInMinutes = Math.round(video.duration / 60);
                handleInputChange('duration', durationInMinutes);
      }
    };
    video.onerror = () => {
      window.URL.revokeObjectURL(video.src);
          };
    video.src = URL.createObjectURL(file);
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (event: React.DragEvent) => {
    event.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setIsDragOver(false);
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const triggerFileInput = () => {
    const fileInput = document.getElementById('video-file-input') as HTMLInputElement;
    fileInput?.click();
  };

  const generateLessonSuggestions = () => {
    const courseTitle = Array.isArray(courses) ? courses.find(c => c.id === formData.course)?.title || '' : '';
    
    const suggestions = [
      `Introduction to ${courseTitle}`,
      `${courseTitle} - Key Concepts`,
      `Understanding ${courseTitle} Fundamentals`,
      `Advanced ${courseTitle} Strategies`,
      `${courseTitle} - Practical Examples`,
      `${courseTitle} - Risk Management`,
      `${courseTitle} - Market Analysis`,
      `${courseTitle} - Trading Psychology`,
    ];

    return suggestions;
  };

  const getVideoPreview = () => {
    // Show YouTube preview
    if (formData.video_source === 'youtube' && formData.video_url) {
      const videoId = extractYouTubeId(formData.video_url);
      if (videoId) {
        return (
          <div className="mt-2">
            <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden">
              <iframe
                src={`https://www.youtube.com/embed/${videoId}`}
                className="w-full h-full"
                frameBorder="0"
                allowFullScreen
              />
            </div>
          </div>
        );
      }
    }
    
    // Show Vimeo preview
    if (formData.video_source === 'vimeo' && formData.video_url) {
      const vimeoRegex = /vimeo\.com\/(\d+)/;
      const match = formData.video_url.match(vimeoRegex);
      if (match && match[1]) {
        return (
          <div className="mt-2">
            <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden">
              <iframe
                src={`https://player.vimeo.com/video/${match[1]}`}
                className="w-full h-full"
                frameBorder="0"
                allowFullScreen
              />
            </div>
          </div>
        );
      }
    }
    
    return null;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {lesson ? 'Edit Lesson' : 'Create New Lesson'}
            </h2>
            <p className="text-gray-700 mt-1">
              {lesson ? 'Update lesson details and content' : 'Add a new lesson to your course'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column - Basic Info */}
            <div className="space-y-6">
              {/* Lesson Title */}
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Lesson Title *
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black"
                  placeholder="e.g., Introduction to Forex Trading"
                  required
                />
                
                {/* Quick Suggestions */}
                {formData.course && !formData.title && (
                  <div className="mt-2">
                    <p className="text-xs text-gray-700 mb-1">Quick suggestions:</p>
                    <div className="flex flex-wrap gap-1">
                      {generateLessonSuggestions().slice(0, 3).map((suggestion, index) => (
                        <button
                          key={index}
                          type="button"
                          onClick={() => handleInputChange('title', suggestion)}
                          className="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded text-gray-700"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Lesson Slug */}
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Lesson Slug *
                </label>
                <input
                  type="text"
                  value={formData.slug}
                  onChange={(e) => handleInputChange('slug', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black"
                  placeholder="lesson-url-slug (auto-generated from title)"
                  required
                />
                <p className="mt-1 text-sm text-gray-500">
                  URL-friendly version of the title. Used in lesson URLs.
                </p>
              </div>

              {/* Course Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Course *
                </label>
                {(!Array.isArray(courses) || courses.length === 0) ? (
                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-yellow-800 text-sm">
                      No courses available. You need to create a course first before adding lessons.
                    </p>
                    <button
                      type="button"
                      onClick={() => window.open('/admin/courses', '_blank')}
                      className="mt-2 text-sm text-yellow-700 hover:text-yellow-800 underline"
                    >
                      Create a course first →
                    </button>
                  </div>
                ) : (
                  <select
                    value={formData.course}
                    onChange={(e) => handleInputChange('course', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black"
                    required
                  >
                    <option value="">Select a course</option>
                    {Array.isArray(courses) && courses.map(course => (
                      <option key={course.id} value={course.id}>
                        {course.title}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* Lesson Order & Duration */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Lesson Order
                  </label>
                  <input
                    type="number"
                    value={formData.order}
                    onChange={(e) => {
                      const val = e.target.value;
                      // Allow empty string while typing, convert to number on blur
                      if (val === '') {
                        handleInputChange('order', 1);
                      } else {
                        const num = parseInt(val, 10);
                        handleInputChange('order', isNaN(num) ? 1 : Math.max(1, num));
                      }
                    }}
                    onBlur={(e) => {
                      // Ensure valid number on blur
                      if (e.target.value === '' || parseInt(e.target.value, 10) < 1) {
                        handleInputChange('order', 1);
                      }
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black"
                    min="1"
                    placeholder="1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Duration (minutes)
                  </label>
                  <input
                    type="number"
                    value={formData.duration}
                    onChange={(e) => {
                      const val = e.target.value;
                      // Allow empty string while typing
                      if (val === '') {
                        handleInputChange('duration', 0);
                      } else {
                        const num = parseInt(val, 10);
                        handleInputChange('duration', isNaN(num) ? 0 : Math.max(0, num));
                      }
                    }}
                    onBlur={(e) => {
                      // Ensure valid number on blur
                      if (e.target.value === '') {
                        handleInputChange('duration', 0);
                      }
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black"
                    min="0"
                    placeholder="Auto-detected for uploads"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    {formData.video_source === 'upload' ? 'Auto-detected from video file' : 'Enter video length in minutes'}
                  </p>
                </div>
              </div>

              {/* Preview Checkbox */}
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_preview}
                    onChange={(e) => handleInputChange('is_preview', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-900">
                    Make this a preview lesson (viewable by non-premium users)
                  </span>
                </label>
              </div>
            </div>

            {/* Right Column - Video & Content */}
            <div className="space-y-6">
              {/* Video Source */}
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Video Source
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { 
                      value: 'upload', 
                      label: 'Upload', 
                      desc: 'Upload video file',
                      icon: (
                        <svg className="w-6 h-6 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                      )
                    },
                    { 
                      value: 'youtube', 
                      label: 'YouTube', 
                      desc: 'YouTube URL',
                      icon: (
                        <svg className="w-6 h-6 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      )
                    },
                    { 
                      value: 'vimeo', 
                      label: 'Vimeo', 
                      desc: 'Vimeo URL',
                      icon: (
                        <svg className="w-6 h-6 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                      )
                    },
                  ].map(source => (
                    <label
                      key={source.value}
                      className={`border rounded-lg p-3 cursor-pointer transition-colors ${
                        formData.video_source === source.value
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <input
                        type="radio"
                        name="video_source"
                        value={source.value}
                        checked={formData.video_source === source.value}
                        onChange={(e) => handleInputChange('video_source', e.target.value)}
                        className="sr-only"
                      />
                      <div className="text-center">
                        <div className={formData.video_source === source.value ? 'text-blue-600' : 'text-gray-600'}>
                          {source.icon}
                        </div>
                        <div className="text-xs font-medium text-gray-900">{source.label.split(' ')[1]}</div>
                        <div className="text-xs text-gray-700">{source.desc}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Video URL (for YouTube/Vimeo) */}
              {(formData.video_source === 'youtube' || formData.video_source === 'vimeo') && (
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Video URL *
                  </label>
                  <input
                    type="url"
                    value={formData.video_url}
                    onChange={(e) => handleInputChange('video_url', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black"
                    placeholder={formData.video_source === 'youtube' 
                      ? "https://youtube.com/watch?v=..." 
                      : "https://vimeo.com/..."
                    }
                    required
                  />
                  {getVideoPreview()}
                </div>
              )}

              {/* File Upload (for uploaded videos) */}
              {formData.video_source === 'upload' && (
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Video File {selectedFile || (lesson && (lesson as any).video_file_url) ? (
                      <span className="text-green-600">✓</span>
                    ) : (
                      <span className="text-red-600">*</span>
                    )}
                  </label>
                  
                  {/* Show existing video preview first if editing */}
                  {!selectedFile && lesson && (lesson as any).video_file_url && (
                    <div className="mb-4">
                      <div className="aspect-video bg-gray-900 rounded-lg overflow-hidden">
                        <video
                          controls
                          className="w-full h-full"
                          src={(lesson as any).video_file_url}
                        >
                          Your browser does not support the video tag.
                        </video>
                      </div>
                      <p className="text-xs text-gray-500 mt-2 text-center">
                        Current video • Upload a new file to replace
                      </p>
                    </div>
                  )}
                  
                  <div 
                    className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                      isDragOver 
                        ? 'border-blue-400 bg-blue-50' 
                        : selectedFile 
                          ? 'border-green-400 bg-green-50' 
                          : 'border-gray-300 hover:border-gray-400'
                    }`}
                    onClick={triggerFileInput}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  >
                    {selectedFile ? (
                      <div>
                        <svg className="mx-auto h-12 w-12 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        <p className="mt-2 text-sm text-green-700 font-medium">
                          {selectedFile.name}
                        </p>
                        <p className="text-xs text-green-600">
                          {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Click to change file
                        </p>
                      </div>
                    ) : (
                      <div>
                        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        <p className="mt-2 text-sm text-gray-700">
                          {isDragOver ? 'Drop video file here' : 'Click to upload or drag and drop'}
                        </p>
                        <p className="text-xs text-gray-700">MP4, MOV, AVI up to 500MB</p>
                      </div>
                    )}
                    <input
                      id="video-file-input"
                      type="file"
                      accept="video/*"
                      className="hidden"
                      onChange={handleFileSelect}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Description */}
          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Lesson Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black"
              placeholder="Describe what students will learn in this lesson..."
            />
          </div>

          {/* Lesson Notes */}
          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Lesson Notes (Optional)
            </label>
            <textarea
              value={formData.lesson_notes}
              onChange={(e) => handleInputChange('lesson_notes', e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black"
              placeholder="Additional notes, PDF content, or supplementary materials..."
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 mt-8 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Saving...
                </>
              ) : (
                <>
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  {lesson ? 'Update Lesson' : 'Create Lesson'}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
