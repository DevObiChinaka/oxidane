/**
 * Centralized API utilities with automatic authentication handling
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface FetchOptions extends RequestInit {
  requiresAuth?: boolean;
}

/**
 * Custom fetch wrapper that handles authentication automatically
 * - Adds Authorization header if token exists
 * - Redirects to login on 401 (Unauthorized)
 * - Preserves current path for post-login redirect
 */
export async function apiFetch(
  endpoint: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { requiresAuth = true, headers = {}, ...restOptions } = options;

  // Build request headers
  const requestHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(headers as Record<string, string>),
  };

  // Add auth token if required
  if (requiresAuth) {
    const token = localStorage.getItem('access_token');
    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    }
  }

  // Make the request
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...restOptions,
    headers: requestHeaders,
  });

  // Handle 401 Unauthorized globally
  if (response.status === 401 && typeof window !== 'undefined') {
    // Clear tokens
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    // Redirect to login with current path for post-login redirect
    const currentPath = window.location.pathname;
    const redirectParam = currentPath !== '/' ? `?redirect=${currentPath}` : '';
    window.location.href = `/auth/login${redirectParam}`;
    
    // Throw to prevent further processing
    throw new Error('Unauthorized - redirecting to login');
  }

  return response;
}

/**
 * Convenience method for GET requests
 */
export async function apiGet(endpoint: string, requiresAuth = true): Promise<Response> {
  return apiFetch(endpoint, { method: 'GET', requiresAuth });
}

/**
 * Convenience method for POST requests
 */
export async function apiPost(
  endpoint: string,
  data?: any,
  requiresAuth = true
): Promise<Response> {
  return apiFetch(endpoint, {
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
    requiresAuth,
  });
}

/**
 * Convenience method for PUT requests
 */
export async function apiPut(
  endpoint: string,
  data?: any,
  requiresAuth = true
): Promise<Response> {
  return apiFetch(endpoint, {
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
    requiresAuth,
  });
}

/**
 * Convenience method for DELETE requests
 */
export async function apiDelete(endpoint: string, requiresAuth = true): Promise<Response> {
  return apiFetch(endpoint, { method: 'DELETE', requiresAuth });
}

/**
 * Get the full API URL for a given endpoint
 */
export function getApiUrl(endpoint: string): string {
  return endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
}
