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

    console.log(`🔍 Testing: ${options.method || 'GET'} ${url}`);
    
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
    console.log('\n🔐 Testing Authentication...');
    
    // Test admin login
    const loginResponse = await this.makeRequest('/api/admin-auth/login/', {
      method: 'POST',
      body: JSON.stringify({
        username: 'admin',
        password: 'admin123'
      })
    });

    console.log('Login Response:', loginResponse);
    
    if (loginResponse.body?.token) {
      this.authToken = loginResponse.body.token;
      console.log('✅ Authentication successful');
    } else {
      console.log('❌ Authentication failed');
    }

    return loginResponse;
  }

  // Telegram Groups API Tests
  async testTelegramGroupsAPI() {
    console.log('\n📱 Testing Telegram Groups API...');

    // Test 1: Get all groups
    console.log('\n1. GET /api/admin/telegram/groups/');
    const getGroupsResponse = await this.makeRequest('/api/admin/telegram/groups/');
    console.log('Get Groups Response:', getGroupsResponse);

    // Test 2: Create new group
    console.log('\n2. POST /api/admin/telegram/groups/');
    const createGroupResponse = await this.makeRequest('/api/admin/telegram/groups/', {
      method: 'POST',
      body: JSON.stringify(mockTelegramGroup)
    });
    console.log('Create Group Response:', createGroupResponse);

    let groupId = null;
    if (createGroupResponse.body?.id) {
      groupId = createGroupResponse.body.id;
    }

    // Test 3: Get specific group
    if (groupId) {
      console.log(`\n3. GET /api/admin/telegram/groups/${groupId}/`);
      const getGroupResponse = await this.makeRequest(`/api/admin/telegram/groups/${groupId}/`);
      console.log('Get Specific Group Response:', getGroupResponse);
    }

    // Test 4: Update group
    if (groupId) {
      console.log(`\n4. PATCH /api/admin/telegram/groups/${groupId}/`);
      const updateGroupResponse = await this.makeRequest(`/api/admin/telegram/groups/${groupId}/`, {
        method: 'PATCH',
        body: JSON.stringify({
          name: 'Updated Test VIP Signals',
          description: 'Updated description'
        })
      });
      console.log('Update Group Response:', updateGroupResponse);
    }

    // Test 5: Toggle group status
    if (groupId) {
      console.log(`\n5. PATCH /api/admin/telegram/groups/${groupId}/toggle/`);
      const toggleResponse = await this.makeRequest(`/api/admin/telegram/groups/${groupId}/toggle/`, {
        method: 'PATCH',
        body: JSON.stringify({ is_active: false })
      });
      console.log('Toggle Group Response:', toggleResponse);
    }

    return { getGroupsResponse, createGroupResponse, groupId };
  }

  // Telegram Queue API Tests
  async testTelegramQueueAPI() {
    console.log('\n⏳ Testing Telegram Queue API...');

    // Test 1: Get queue items
    console.log('\n1. GET /api/admin/telegram/queue/');
    const getQueueResponse = await this.makeRequest('/api/admin/telegram/queue/');
    console.log('Get Queue Response:', getQueueResponse);

    // Test 2: Create queue item
    console.log('\n2. POST /api/admin/telegram/queue/');
    const createQueueResponse = await this.makeRequest('/api/admin/telegram/queue/', {
      method: 'POST',
      body: JSON.stringify(mockQueueItem)
    });
    console.log('Create Queue Item Response:', createQueueResponse);

    let queueItemId = null;
    if (createQueueResponse.body?.id) {
      queueItemId = createQueueResponse.body.id;
    }

    // Test 3: Get queue statistics
    console.log('\n3. GET /api/admin/telegram/queue/stats/');
    const getStatsResponse = await this.makeRequest('/api/admin/telegram/queue/stats/');
    console.log('Get Queue Stats Response:', getStatsResponse);

    // Test 4: Retry queue item
    if (queueItemId) {
      console.log(`\n4. POST /api/admin/telegram/queue/${queueItemId}/retry/`);
      const retryResponse = await this.makeRequest(`/api/admin/telegram/queue/${queueItemId}/retry/`, {
        method: 'POST'
      });
      console.log('Retry Queue Item Response:', retryResponse);
    }

    // Test 5: Cancel queue item
    if (queueItemId) {
      console.log(`\n5. POST /api/admin/telegram/queue/${queueItemId}/cancel/`);
      const cancelResponse = await this.makeRequest(`/api/admin/telegram/queue/${queueItemId}/cancel/`, {
        method: 'POST',
        body: JSON.stringify({ reason: 'Test cancellation' })
      });
      console.log('Cancel Queue Item Response:', cancelResponse);
    }

    // Test 6: Bulk operations
    console.log('\n6. POST /api/admin/telegram/queue/bulk-retry/');
    const bulkRetryResponse = await this.makeRequest('/api/admin/telegram/queue/bulk-retry/', {
      method: 'POST',
      body: JSON.stringify({
        item_ids: queueItemId ? [queueItemId] : ['test_item_1', 'test_item_2']
      })
    });
    console.log('Bulk Retry Response:', bulkRetryResponse);

    return { getQueueResponse, createQueueResponse, queueItemId };
  }

  // Bot Status API Tests
  async testBotStatusAPI() {
    console.log('\n🤖 Testing Bot Status API...');

    // Test 1: Get bot status
    console.log('\n1. GET /api/admin/telegram/bot/status/');
    const botStatusResponse = await this.makeRequest('/api/admin/telegram/bot/status/');
    console.log('Bot Status Response:', botStatusResponse);

    // Test 2: Bot health check
    console.log('\n2. GET /api/admin/telegram/bot/health/');
    const healthResponse = await this.makeRequest('/api/admin/telegram/bot/health/');
    console.log('Bot Health Response:', healthResponse);

    // Test 3: Queue controls
    console.log('\n3. POST /api/admin/telegram/queue/pause/');
    const pauseResponse = await this.makeRequest('/api/admin/telegram/queue/pause/', {
      method: 'POST'
    });
    console.log('Pause Queue Response:', pauseResponse);

    console.log('\n4. POST /api/admin/telegram/queue/resume/');
    const resumeResponse = await this.makeRequest('/api/admin/telegram/queue/resume/', {
      method: 'POST'
    });
    console.log('Resume Queue Response:', resumeResponse);

    return { botStatusResponse, healthResponse };
  }

  // Analytics API Tests
  async testAnalyticsAPI() {
    console.log('\n📊 Testing Analytics API...');

    // Test 1: Get telegram analytics
    console.log('\n1. GET /api/admin/telegram/analytics/');
    const analyticsResponse = await this.makeRequest('/api/admin/telegram/analytics/');
    console.log('Analytics Response:', analyticsResponse);

    // Test 2: Get analytics with filters
    console.log('\n2. GET /api/admin/telegram/analytics/?period=daily&days_back=7');
    const filteredAnalyticsResponse = await this.makeRequest('/api/admin/telegram/analytics/?period=daily&days_back=7');
    console.log('Filtered Analytics Response:', filteredAnalyticsResponse);

    return { analyticsResponse, filteredAnalyticsResponse };
  }

  // Cleanup Tests
  async cleanup(groupId) {
    if (groupId) {
      console.log('\n🧹 Cleaning up test data...');
      console.log(`Deleting test group: ${groupId}`);
      
      const deleteResponse = await this.makeRequest(`/api/admin/telegram/groups/${groupId}/`, {
        method: 'DELETE'
      });
      console.log('Delete Group Response:', deleteResponse);
    }
  }

  // Run all tests
  async runAllTests() {
    console.log('🚀 Starting Telegram API Test Suite...');
    console.log('================================================');

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

      console.log('\n✅ All tests completed!');
      console.log('================================================');

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