/**
 * Centralized API configuration for admin frontend
 */

// Ensure consistent API base URL across the application
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

console.log('🌐 API Configuration loaded:', {
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  API_BASE_URL,
  NODE_ENV: process.env.NODE_ENV
});