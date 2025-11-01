#!/usr/bin/env node

/**
 * Simple Telegram API Test Runner
 * Run with: node test-telegram-api.js
 */

const https = require('https');
const http = require('http');

class SimpleTelegramAPITester {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.authToken = null;
    this.testResults = [];
  }

  // Make HTTP request
  async makeRequest(path, options = {}) {
    return new Promise((resolve, reject) => {
      const url = new URL(this.baseURL + path);
      const isHttps = url.protocol === 'https:';
      const client = isHttps ? https : http;

      const requestOptions = {
        hostname: url.hostname,
        port: url.port || (isHttps ? 443 : 80),
        path: url.pathname + url.search,
        method: options.method || 'GET',
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'TelegramAPITester/1.0',
          ...(this.authToken && { Authorization: `Bearer ${this.authToken}` }),
          ...options.headers
        }
      };

      const req = client.request(requestOptions, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          try {
            const jsonData = JSON.parse(data);
            resolve({
              status: res.statusCode,
              statusMessage: res.statusMessage,
              headers: res.headers,
              data: jsonData
            });
          } catch (e) {
            resolve({
              status: res.statusCode,
              statusMessage: res.statusMessage,
              headers: res.headers,
              data: data
            });
          }
        });
      });

      req.on('error', reject);
      
      if (options.body) {
        req.write(JSON.stringify(options.body));
      }
      
      req.end();
    });
  }

  // Log test results
  logTest(name, response, expectedStatus = 200) {
    const success = response.status === expectedStatus || (expectedStatus === 'any' && response.status < 500);
    const status = success ? '✅' : '❌';
    
    console.log(`${status} ${name}`);
    console.log(`   Status: ${response.status} ${response.statusMessage}`);
    
    if (response.data) {
      if (typeof response.data === 'object') {
        console.log(`   Response:`, JSON.stringify(response.data, null, 2).substring(0, 200) + '...');
      } else {
        console.log(`   Response: ${response.data.substring(0, 100)}...`);
      }
    }
    
    this.testResults.push({ name, success, status: response.status, response });
    console.log('');
  }

  // Test basic connectivity
  async testConnectivity() {
    console.log('🔌 Testing Basic Connectivity...');
    console.log('================================');
    
    try {
      const response = await this.makeRequest('/api/health/');
      this.logTest('Health Check', response, 'any');
      return response;
    } catch (error) {
      console.log('❌ Connectivity Test Failed');
      console.log('   Error:', error.message);
      console.log('   Make sure Django server is running on', this.baseURL);
      return null;
    }
  }

  // Test authentication
  async testAuth() {
    console.log('🔐 Testing Authentication...');
    console.log('=============================');
    
    // Test login endpoint exists
    try {
      const response = await this.makeRequest('/api/admin-auth/login/', {
        method: 'POST',
        body: {
          username: 'testadmin',
          password: 'testpass123'
        }
      });
      
      this.logTest('Admin Login Endpoint', response, 'any');
      
      if (response.data && response.data.token) {
        this.authToken = response.data.token;
        console.log('🎫 Auth token acquired for further tests');
      }
      
      return response;
    } catch (error) {
      console.log('❌ Auth test failed:', error.message);
      return null;
    }
  }

  // Test Telegram Groups endpoints
  async testTelegramGroups() {
    console.log('📱 Testing Telegram Groups...');
    console.log('=============================');
    
    // Test GET groups
    try {
      const getResponse = await this.makeRequest('/api/admin/telegram/groups/');
      this.logTest('GET Telegram Groups', getResponse, 'any');
    } catch (error) {
      this.logTest('GET Telegram Groups', { status: 'ERROR', statusMessage: error.message }, 'any');
    }

    // Test POST new group
    try {
      const postResponse = await this.makeRequest('/api/admin/telegram/groups/', {
        method: 'POST',
        body: {
          name: 'Test API Group',
          chat_id: '-1001234567890',
          description: 'Test group created by API tester',
          is_active: true
        }
      });
      this.logTest('POST Create Group', postResponse, 'any');
      
      // If group was created, test other operations
      if (postResponse.data && postResponse.data.id) {
        const groupId = postResponse.data.id;
        
        // Test GET specific group
        try {
          const getOneResponse = await this.makeRequest(`/api/admin/telegram/groups/${groupId}/`);
          this.logTest('GET Specific Group', getOneResponse, 'any');
        } catch (error) {
          this.logTest('GET Specific Group', { status: 'ERROR', statusMessage: error.message }, 'any');
        }
        
        // Test PATCH update
        try {
          const patchResponse = await this.makeRequest(`/api/admin/telegram/groups/${groupId}/`, {
            method: 'PATCH',
            body: {
              description: 'Updated by API tester'
            }
          });
          this.logTest('PATCH Update Group', patchResponse, 'any');
        } catch (error) {
          this.logTest('PATCH Update Group', { status: 'ERROR', statusMessage: error.message }, 'any');
        }
        
        // Test DELETE
        try {
          const deleteResponse = await this.makeRequest(`/api/admin/telegram/groups/${groupId}/`, {
            method: 'DELETE'
          });
          this.logTest('DELETE Group', deleteResponse, 'any');
        } catch (error) {
          this.logTest('DELETE Group', { status: 'ERROR', statusMessage: error.message }, 'any');
        }
      }
    } catch (error) {
      this.logTest('POST Create Group', { status: 'ERROR', statusMessage: error.message }, 'any');
    }
  }

  // Test Telegram Queue endpoints
  async testTelegramQueue() {
    console.log('⏳ Testing Telegram Queue...');
    console.log('============================');
    
    // Test GET queue
    try {
      const getResponse = await this.makeRequest('/api/admin/telegram/queue/');
      this.logTest('GET Queue Items', getResponse, 'any');
    } catch (error) {
      this.logTest('GET Queue Items', { status: 'ERROR', statusMessage: error.message }, 'any');
    }

    // Test queue stats
    try {
      const statsResponse = await this.makeRequest('/api/admin/telegram/queue/stats/');
      this.logTest('GET Queue Stats', statsResponse, 'any');
    } catch (error) {
      this.logTest('GET Queue Stats', { status: 'ERROR', statusMessage: error.message }, 'any');
    }

    // Test POST new queue item
    try {
      const postResponse = await this.makeRequest('/api/admin/telegram/queue/', {
        method: 'POST',
        body: {
          user_id: 'test_user_123',
          action_type: 'add_to_group',
          group_name: 'Test Group',
          priority: 'normal'
        }
      });
      this.logTest('POST Queue Item', postResponse, 'any');
    } catch (error) {
      this.logTest('POST Queue Item', { status: 'ERROR', statusMessage: error.message }, 'any');
    }

    // Test bulk operations
    try {
      const bulkResponse = await this.makeRequest('/api/admin/telegram/queue/bulk-retry/', {
        method: 'POST',
        body: {
          item_ids: ['test_id_1', 'test_id_2']
        }
      });
      this.logTest('POST Bulk Retry', bulkResponse, 'any');
    } catch (error) {
      this.logTest('POST Bulk Retry', { status: 'ERROR', statusMessage: error.message }, 'any');
    }
  }

  // Test Bot Status endpoints
  async testBotStatus() {
    console.log('🤖 Testing Bot Status...');
    console.log('========================');
    
    // Test bot status
    try {
      const statusResponse = await this.makeRequest('/api/admin/telegram/bot/status/');
      this.logTest('GET Bot Status', statusResponse, 'any');
    } catch (error) {
      this.logTest('GET Bot Status', { status: 'ERROR', statusMessage: error.message }, 'any');
    }

    // Test bot health
    try {
      const healthResponse = await this.makeRequest('/api/admin/telegram/bot/health/');
      this.logTest('GET Bot Health', healthResponse, 'any');
    } catch (error) {
      this.logTest('GET Bot Health', { status: 'ERROR', statusMessage: error.message }, 'any');
    }

    // Test queue controls
    try {
      const pauseResponse = await this.makeRequest('/api/admin/telegram/queue/pause/', {
        method: 'POST'
      });
      this.logTest('POST Pause Queue', pauseResponse, 'any');
    } catch (error) {
      this.logTest('POST Pause Queue', { status: 'ERROR', statusMessage: error.message }, 'any');
    }

    try {
      const resumeResponse = await this.makeRequest('/api/admin/telegram/queue/resume/', {
        method: 'POST'
      });
      this.logTest('POST Resume Queue', resumeResponse, 'any');
    } catch (error) {
      this.logTest('POST Resume Queue', { status: 'ERROR', statusMessage: error.message }, 'any');
    }
  }

  // Test Analytics endpoints
  async testAnalytics() {
    console.log('📊 Testing Analytics...');
    console.log('=======================');
    
    try {
      const analyticsResponse = await this.makeRequest('/api/admin/telegram/analytics/');
      this.logTest('GET Analytics', analyticsResponse, 'any');
    } catch (error) {
      this.logTest('GET Analytics', { status: 'ERROR', statusMessage: error.message }, 'any');
    }

    try {
      const filteredResponse = await this.makeRequest('/api/admin/telegram/analytics/?period=daily&days_back=7');
      this.logTest('GET Filtered Analytics', filteredResponse, 'any');
    } catch (error) {
      this.logTest('GET Filtered Analytics', { status: 'ERROR', statusMessage: error.message }, 'any');
    }
  }

  // Generate test report
  generateReport() {
    console.log('📋 Test Results Summary');
    console.log('=======================');
    
    const total = this.testResults.length;
    const passed = this.testResults.filter(t => t.success).length;
    const failed = total - passed;
    
    console.log(`Total Tests: ${total}`);
    console.log(`Passed: ${passed} ✅`);
    console.log(`Failed: ${failed} ❌`);
    console.log(`Success Rate: ${((passed / total) * 100).toFixed(1)}%`);
    
    if (failed > 0) {
      console.log('\nFailed Tests:');
      this.testResults.filter(t => !t.success).forEach(t => {
        console.log(`- ${t.name} (Status: ${t.status})`);
      });
    }

    console.log('\nEndpoint Coverage:');
    const endpoints = [...new Set(this.testResults.map(t => t.name.split(' ')[1] || t.name))];
    endpoints.forEach(endpoint => {
      const tests = this.testResults.filter(t => t.name.includes(endpoint));
      const endpointPassed = tests.filter(t => t.success).length;
      const endpointTotal = tests.length;
      console.log(`- ${endpoint}: ${endpointPassed}/${endpointTotal} tests passed`);
    });
  }

  // Run all tests
  async runAllTests() {
    console.log('🚀 Telegram API Test Suite');
    console.log('===========================');
    console.log(`Testing against: ${this.baseURL}`);
    console.log(`Started at: ${new Date().toISOString()}\n`);
    
    // Basic connectivity
    const connectivity = await this.testConnectivity();
    if (!connectivity) {
      console.log('💥 Cannot connect to server. Stopping tests.');
      return;
    }

    // Authentication
    await this.testAuth();

    // API endpoints
    await this.testTelegramGroups();
    await this.testTelegramQueue();
    await this.testBotStatus();
    await this.testAnalytics();

    // Generate report
    this.generateReport();
    
    console.log(`\n🏁 Testing completed at: ${new Date().toISOString()}`);
  }
}

// CLI interface
if (require.main === module) {
  const args = process.argv.slice(2);
  const baseURL = args[0] || 'http://localhost:8000';
  
  console.log('Starting Telegram API Tests...');
  console.log('Usage: node test-telegram-api.js [base_url]');
  console.log(`Using base URL: ${baseURL}\n`);
  
  const tester = new SimpleTelegramAPITester(baseURL);
  tester.runAllTests().catch(console.error);
}

module.exports = { SimpleTelegramAPITester };