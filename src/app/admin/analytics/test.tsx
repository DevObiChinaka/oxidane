'use client';

import { useState } from 'react';
import { AdminAPIClient } from '../utils/api';

export default function AnalyticsTest() {
  const [testResult, setTestResult] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const testAnalyticsAPI = async () => {
    setLoading(true);
    setTestResult('Testing analytics API...');

    try {
      const startTime = Date.now();
      const adminClient = new AdminAPIClient();
      const response = await adminClient.getDashboardAnalytics();
      const endTime = Date.now();
      
      const responseTime = endTime - startTime;
      
      setTestResult(`
✅ Analytics API Test Successful!

Response Time: ${responseTime}ms
Generated At: ${response.generated_at}

Course Metrics:
- Total Courses: ${response.course_metrics.total_courses}
- Published Rate: ${response.course_metrics.publish_rate}%
- Free/Premium: ${response.course_metrics.free_courses}/${response.course_metrics.premium_courses}

Content Metrics:
- Total Lessons: ${response.content_metrics.total_lessons}
- Duration: ${response.content_metrics.total_duration_hours} hours
- Avg Lessons/Course: ${response.content_metrics.avg_lessons_per_course}

User Metrics:
- Total Users: ${response.user_metrics.total_users}
- Verification Rate: ${response.user_metrics.verification_rate}%
- Recent Signups (7d): ${response.user_metrics.recent_registrations_7d}

Popular Courses: ${response.popular_courses.length} courses found
Growth Data: ${response.growth_metrics.monthly_courses.length} months of course data

🎯 All metrics loaded successfully!
      `);
    } catch (error) {
      setTestResult(`
❌ Analytics API Test Failed!

Error: ${error instanceof Error ? error.message : 'Unknown error'}

This could be due to:
1. Backend server not running
2. Authentication issues
3. API endpoint not accessible
4. Network connectivity issues

Please check:
- Django server is running on port 8000
- You're logged in as an admin user
- CORS settings are configured properly
      `);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Analytics API Test</h1>
      
      <button
        onClick={testAnalyticsAPI}
        disabled={loading}
        className={`px-6 py-3 rounded-lg font-medium ${
          loading
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-500 hover:bg-blue-600 text-white'
        }`}
      >
        {loading ? 'Testing...' : 'Test Analytics API'}
      </button>

      {testResult && (
        <div className="mt-6 p-4 bg-gray-100 rounded-lg">
          <pre className="whitespace-pre-wrap text-sm font-mono">
            {testResult}
          </pre>
        </div>
      )}
    </div>
  );
}