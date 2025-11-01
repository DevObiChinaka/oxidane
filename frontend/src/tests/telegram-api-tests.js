/**
 * Telegram API Test Suite
 * Tests all Telegram management endpoints and functionality
 */

// Mock data for testing
const mockTelegramGroup = {
  name: 'Test VIP Signals',
  chat_id: '-1001234567890',
  description: 'Test group for API validation',
  is_active: true
};

const mockQueueItem = {
  user_id: 'test_user_1',
  subscription_id: 'test_sub_1',
  action_type: 'add_to_group',
  group_name: 'Test VIP Signals',
  priority: 'normal'
};

class TelegramAPITester {
  constructor(baseURL = 'http://localhost:8000', authToken = '') {
    this.baseURL = baseURL;
    this.authToken = authToken;
  }

  async makeRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(this.authToken && { Authorization: `Bearer ${this.authToken}` }),
      ...options.headers
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers
      });

      const responseData = {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        body: null
      };

      // Try to parse response body
      try {
        const text = await response.text();
        try {
          responseData.body = JSON.parse(text);
        } catch (jsonError) {
          responseData.body = text;
        }
      } catch (textError) {
        responseData.body = 'Unable to read response body';
      }

      return responseData;
    } catch (error) {
      console.error(`❌ Request failed: ${error}`);
      throw error;
    }
  }

  // Authentication Tests
  async testAuthentication() {

    // Test admin login
    const loginResponse = await this.makeRequest('/api/admin-auth/login/', {
      method: 'POST',
      body: JSON.stringify({
        username: 'admin',
        password: 'admin123'
      })
    });

    if (loginResponse.body?.token) {
      this.authToken = loginResponse.body.token;

    } else {

    }

    return loginResponse;
  }

  // Telegram Groups API Tests
  async testTelegramGroupsAPI() {

    // Test 1: Get all groups

    const getGroupsResponse = await this.makeRequest('/api/admin/telegram/groups/');

    // Test 2: Create new group

    const createGroupResponse = await this.makeRequest('/api/admin/telegram/groups/', {
      method: 'POST',
      body: JSON.stringify(mockTelegramGroup)
    });

    let groupId = null;
    if (createGroupResponse.body?.id) {
      groupId = createGroupResponse.body.id;
    }

    // Test 3: Get specific group
    if (groupId) {

      const getGroupResponse = await this.makeRequest(`/api/admin/telegram/groups/${groupId}/`);

    }

    // Test 4: Update group
    if (groupId) {

      const updateGroupResponse = await this.makeRequest(`/api/admin/telegram/groups/${groupId}/`, {
        method: 'PATCH',
        body: JSON.stringify({
          name: 'Updated Test VIP Signals',
          description: 'Updated description'
        })
      });

    }

    // Test 5: Toggle group status
    if (groupId) {

      const toggleResponse = await this.makeRequest(`/api/admin/telegram/groups/${groupId}/toggle/`, {
        method: 'PATCH',
        body: JSON.stringify({ is_active: false })
      });

    }

    return { getGroupsResponse, createGroupResponse, groupId };
  }

  // Telegram Queue API Tests
  async testTelegramQueueAPI() {

    // Test 1: Get queue items

    const getQueueResponse = await this.makeRequest('/api/admin/telegram/queue/');

    // Test 2: Create queue item

    const createQueueResponse = await this.makeRequest('/api/admin/telegram/queue/', {
      method: 'POST',
      body: JSON.stringify(mockQueueItem)
    });

    let queueItemId = null;
    if (createQueueResponse.body?.id) {
      queueItemId = createQueueResponse.body.id;
    }

    // Test 3: Get queue statistics

    const getStatsResponse = await this.makeRequest('/api/admin/telegram/queue/stats/');

    // Test 4: Retry queue item
    if (queueItemId) {

      const retryResponse = await this.makeRequest(`/api/admin/telegram/queue/${queueItemId}/retry/`, {
        method: 'POST'
      });

    }

    // Test 5: Cancel queue item
    if (queueItemId) {

      const cancelResponse = await this.makeRequest(`/api/admin/telegram/queue/${queueItemId}/cancel/`, {
        method: 'POST',
        body: JSON.stringify({ reason: 'Test cancellation' })
      });

    }

    // Test 6: Bulk operations

    const bulkRetryResponse = await this.makeRequest('/api/admin/telegram/queue/bulk-retry/', {
      method: 'POST',
      body: JSON.stringify({
        item_ids: queueItemId ? [queueItemId] : ['test_item_1', 'test_item_2']
      })
    });

    return { getQueueResponse, createQueueResponse, queueItemId };
  }

  // Bot Status API Tests
  async testBotStatusAPI() {

    // Test 1: Get bot status

    const botStatusResponse = await this.makeRequest('/api/admin/telegram/bot/status/');

    // Test 2: Bot health check

    const healthResponse = await this.makeRequest('/api/admin/telegram/bot/health/');

    // Test 3: Queue controls

    const pauseResponse = await this.makeRequest('/api/admin/telegram/queue/pause/', {
      method: 'POST'
    });

    const resumeResponse = await this.makeRequest('/api/admin/telegram/queue/resume/', {
      method: 'POST'
    });

    return { botStatusResponse, healthResponse };
  }

  // Analytics API Tests
  async testAnalyticsAPI() {

    // Test 1: Get telegram analytics

    const analyticsResponse = await this.makeRequest('/api/admin/telegram/analytics/');

    // Test 2: Get analytics with filters

    const filteredAnalyticsResponse = await this.makeRequest('/api/admin/telegram/analytics/?period=daily&days_back=7');

    return { analyticsResponse, filteredAnalyticsResponse };
  }

  // Cleanup Tests
  async cleanup(groupId) {
    if (groupId) {

      const deleteResponse = await this.makeRequest(`/api/admin/telegram/groups/${groupId}/`, {
        method: 'DELETE'
      });

    }
  }

  // Run all tests
  async runAllTests() {

    try {
      // Authentication
      await this.testAuthentication();

      // Main API Tests
      const groupResults = await this.testTelegramGroupsAPI();
      const queueResults = await this.testTelegramQueueAPI();
      await this.testBotStatusAPI();
      await this.testAnalyticsAPI();

      // Cleanup
      await this.cleanup(groupResults.groupId);

    } catch (error) {
      console.error('❌ Test suite failed:', error);
    }
  }
}

// Check if running in Node.js environment
if (typeof module !== 'undefined' && module.exports) {
  // Node.js environment - export for use in other files
  module.exports = { TelegramAPITester };
  
  // Run tests if this file is executed directly
  if (require.main === module) {
    const tester = new TelegramAPITester();
    tester.runAllTests();
  }
} else if (typeof window !== 'undefined') {
  // Browser environment - make available globally
  window.TelegramAPITester = TelegramAPITester;
  
  // Auto-run tests in browser if desired
  console.log('TelegramAPITester available globally. Use new TelegramAPITester().runAllTests() to start testing.');
}