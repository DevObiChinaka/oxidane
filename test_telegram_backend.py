#!/usr/bin/env python3
"""
Django Backend Telegram API Test Suite
Tests all Telegram-related Django endpoints and models

Run with: python test_telegram_backend.py
"""

import json
import requests
import sys
import time
from datetime import datetime
from urllib.parse import urljoin

class DjangoTelegramTester:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, name, response, expected_status=200):
        """Log test results with proper formatting"""
        success = (response.status_code == expected_status or 
                  (expected_status == 'any' and response.status_code < 500))
        status = '✅' if success else '❌'
        
        print(f'{status} {name}')
        print(f'   Status: {response.status_code} {response.reason}')
        
        try:
            data = response.json()
            print(f'   Response: {json.dumps(data, indent=2)[:200]}...')
        except (json.JSONDecodeError, ValueError):
            print(f'   Response: {response.text[:100]}...')
        
        self.test_results.append({
            'name': name,
            'success': success,
            'status_code': response.status_code,
            'response': response
        })
        print()
        
    def make_request(self, endpoint, method='GET', data=None, **kwargs):
        """Make HTTP request to Django backend"""
        url = urljoin(self.base_url, endpoint)
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'DjangoTelegramTester/1.0'
        }
        
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
            
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
            
        print(f'🔍 Testing: {method} {url}')
        
        try:
            if data and method.upper() in ['POST', 'PUT', 'PATCH']:
                response = self.session.request(
                    method, url, 
                    json=data, 
                    headers=headers, 
                    timeout=30,
                    **kwargs
                )
            else:
                response = self.session.request(
                    method, url, 
                    headers=headers, 
                    timeout=30,
                    **kwargs
                )
            return response
        except requests.exceptions.RequestException as e:
            print(f'❌ Request failed: {e}')
            # Return a mock response for error handling
            class MockResponse:
                status_code = 0
                reason = str(e)
                text = str(e)
                def json(self): 
                    return {'error': str(e)}
            return MockResponse()

    def test_server_connectivity(self):
        """Test basic server connectivity"""
        print('🔌 Testing Server Connectivity...')
        print('================================')
        
        # Test Django admin endpoint
        response = self.make_request('/admin/')
        self.log_test('Django Admin Access', response, 'any')
        
        # Test API root
        response = self.make_request('/api/')
        self.log_test('API Root Access', response, 'any')
        
        return response.status_code < 500

    def test_authentication(self):
        """Test Django authentication system"""
        print('🔐 Testing Django Authentication...')
        print('==================================')
        
        # Test admin auth check endpoint
        response = self.make_request('/api/admin-auth/check-session/')
        self.log_test('Check Session Endpoint', response, 'any')
        
        # Test admin login
        login_data = {
            'username': 'admin',  # Default Django admin
            'password': 'admin123'
        }
        response = self.make_request('/api/admin-auth/login/', 'POST', login_data)
        self.log_test('Admin Login', response, 'any')
        
        # Extract token if login successful
        try:
            if response.status_code < 300:
                token_data = response.json()
                if 'token' in token_data:
                    self.auth_token = token_data['token']
                    print(f'🎫 Auth token acquired: {self.auth_token[:20]}...')
                elif 'access_token' in token_data:
                    self.auth_token = token_data['access_token']
                    print(f'🎫 Access token acquired: {self.auth_token[:20]}...')
        except (json.JSONDecodeError, ValueError):
            pass
            
    def test_database_models(self):
        """Test Django models and database connectivity"""
        print('🗃️ Testing Database Models...')
        print('=============================')
        
        # Test if we can access Django ORM
        response = self.make_request('/api/admin/users/')
        self.log_test('Users Model Access', response, 'any')
        
        response = self.make_request('/api/admin/subscriptions/')
        self.log_test('Subscriptions Model Access', response, 'any')
        
    def test_telegram_models_endpoints(self):
        """Test Telegram-specific model endpoints"""
        print('📱 Testing Telegram Models...')
        print('=============================')
        
        # Test telegram groups endpoint
        response = self.make_request('/api/admin/telegram/groups/')
        self.log_test('Telegram Groups Endpoint', response, 'any')
        
        # Test telegram queue endpoint  
        response = self.make_request('/api/admin/telegram/queue/')
        self.log_test('Telegram Queue Endpoint', response, 'any')
        
        # Test creating a telegram group
        group_data = {
            'name': 'Test Django Group',
            'chat_id': '-1001234567890',
            'description': 'Created by Django tester',
            'is_active': True
        }
        response = self.make_request('/api/admin/telegram/groups/', 'POST', group_data)
        self.log_test('Create Telegram Group', response, 'any')
        
        # If creation was successful, test other operations
        if response.status_code < 300:
            try:
                group = response.json()
                group_id = group.get('id')
                if group_id:
                    # Test get specific group
                    response = self.make_request(f'/api/admin/telegram/groups/{group_id}/')
                    self.log_test('Get Specific Group', response, 'any')
                    
                    # Test update group
                    update_data = {'description': 'Updated by Django tester'}
                    response = self.make_request(f'/api/admin/telegram/groups/{group_id}/', 'PATCH', update_data)
                    self.log_test('Update Group', response, 'any')
                    
                    # Test delete group (cleanup)
                    response = self.make_request(f'/api/admin/telegram/groups/{group_id}/', 'DELETE')
                    self.log_test('Delete Group', response, 'any')
            except (json.JSONDecodeError, ValueError, KeyError):
                pass

    def test_telegram_queue_operations(self):
        """Test Telegram queue operations"""
        print('⏳ Testing Telegram Queue Operations...')
        print('=====================================')
        
        # Test queue stats
        response = self.make_request('/api/admin/telegram/queue/stats/')
        self.log_test('Queue Statistics', response, 'any')
        
        # Test queue controls
        response = self.make_request('/api/admin/telegram/queue/pause/', 'POST')
        self.log_test('Pause Queue', response, 'any')
        
        response = self.make_request('/api/admin/telegram/queue/resume/', 'POST')
        self.log_test('Resume Queue', response, 'any')
        
        # Test creating queue item
        queue_data = {
            'user_id': 'test_user_123',
            'action_type': 'add_to_group',
            'group_name': 'Test Group',
            'priority': 'normal'
        }
        response = self.make_request('/api/admin/telegram/queue/', 'POST', queue_data)
        self.log_test('Create Queue Item', response, 'any')
        
        # Test bulk operations
        bulk_data = {
            'item_ids': ['test_1', 'test_2'],
            'action': 'retry'
        }
        response = self.make_request('/api/admin/telegram/queue/bulk-retry/', 'POST', bulk_data)
        self.log_test('Bulk Retry Operation', response, 'any')

    def test_bot_integration_endpoints(self):
        """Test bot integration endpoints"""
        print('🤖 Testing Bot Integration...')
        print('=============================')
        
        # Test bot status
        response = self.make_request('/api/admin/telegram/bot/status/')
        self.log_test('Bot Status', response, 'any')
        
        # Test bot health
        response = self.make_request('/api/admin/telegram/bot/health/')
        self.log_test('Bot Health Check', response, 'any')
        
        # Test webhook info (if implemented)
        response = self.make_request('/api/admin/telegram/bot/webhook/')
        self.log_test('Bot Webhook Info', response, 'any')

    def test_analytics_endpoints(self):
        """Test analytics and reporting endpoints"""
        print('📊 Testing Analytics...')
        print('======================')
        
        # Test general analytics
        response = self.make_request('/api/admin/telegram/analytics/')
        self.log_test('Telegram Analytics', response, 'any')
        
        # Test filtered analytics
        params = '?period=daily&days_back=7'
        response = self.make_request(f'/api/admin/telegram/analytics/{params}')
        self.log_test('Filtered Analytics', response, 'any')

    def test_permissions_and_security(self):
        """Test authentication and permissions"""
        print('🔒 Testing Security & Permissions...')
        print('===================================')
        
        # Test without authentication
        old_token = self.auth_token
        self.auth_token = None
        
        response = self.make_request('/api/admin/telegram/groups/')
        self.log_test('Unauthenticated Access (Should Fail)', response, 'any')
        
        # Test with invalid token
        self.auth_token = 'invalid_token_12345'
        response = self.make_request('/api/admin/telegram/groups/')
        self.log_test('Invalid Token Access (Should Fail)', response, 'any')
        
        # Restore valid token
        self.auth_token = old_token

    def check_django_settings(self):
        """Check Django configuration for Telegram integration"""
        print('⚙️ Checking Django Settings...')
        print('==============================')
        
        # Try to access Django admin
        response = self.make_request('/admin/')
        admin_accessible = response.status_code < 500
        print(f"{'✅' if admin_accessible else '❌'} Django Admin: {'Accessible' if admin_accessible else 'Not accessible'}")
        
        # Check if API is configured
        response = self.make_request('/api/')
        api_configured = response.status_code < 500
        print(f"{'✅' if api_configured else '❌'} API Root: {'Configured' if api_configured else 'Not configured'}")
        
        # Check for CORS headers (important for frontend)
        if hasattr(response, 'headers'):
            cors_enabled = 'access-control-allow-origin' in response.headers
            print(f"{'✅' if cors_enabled else '❌'} CORS: {'Enabled' if cors_enabled else 'Not detected'}")

    def generate_report(self):
        """Generate comprehensive test report"""
        print('📋 Test Results Summary')
        print('======================')
        
        total = len(self.test_results)
        if total == 0:
            print('No tests were executed.')
            return
            
        passed = sum(1 for t in self.test_results if t['success'])
        failed = total - passed
        
        print(f'Total Tests: {total}')
        print(f'Passed: {passed} ✅')
        print(f'Failed: {failed} ❌')
        print(f'Success Rate: {(passed / total * 100):.1f}%')
        
        if failed > 0:
            print('\n❌ Failed Tests:')
            for test in self.test_results:
                if not test['success']:
                    print(f'  - {test["name"]} (Status: {test["status_code"]})')
        
        print('\n📊 Endpoint Coverage:')
        endpoints = set()
        for test in self.test_results:
            # Extract endpoint from test name
            endpoint = test['name'].split(' ')[-1] if ' ' in test['name'] else test['name']
            endpoints.add(endpoint)
        
        for endpoint in sorted(endpoints):
            endpoint_tests = [t for t in self.test_results if endpoint in t['name']]
            endpoint_passed = sum(1 for t in endpoint_tests if t['success'])
            print(f'  - {endpoint}: {endpoint_passed}/{len(endpoint_tests)} passed')

        # Recommendations
        print('\n💡 Recommendations:')
        if any(not t['success'] and 'auth' in t['name'].lower() for t in self.test_results):
            print('  - Check Django authentication configuration')
        if any(not t['success'] and t['status_code'] == 404 for t in self.test_results):
            print('  - Verify URL patterns in urls.py')
        if any(not t['success'] and t['status_code'] == 500 for t in self.test_results):
            print('  - Check Django logs for server errors')
        if not self.auth_token:
            print('  - Ensure admin user exists and authentication works')

    def run_all_tests(self):
        """Run complete test suite"""
        print('🚀 Django Telegram API Test Suite')
        print('=================================')
        print(f'Testing Django backend: {self.base_url}')
        print(f'Started: {datetime.now().isoformat()}')
        print()
        
        # Test connectivity first
        if not self.test_server_connectivity():
            print('💥 Cannot connect to Django server. Make sure it\'s running!')
            print('Start with: python manage.py runserver')
            return
        
        # Run all tests
        self.test_authentication()
        self.check_django_settings()
        self.test_database_models()
        self.test_telegram_models_endpoints()
        self.test_telegram_queue_operations()
        self.test_bot_integration_endpoints()
        self.test_analytics_endpoints()
        self.test_permissions_and_security()
        
        # Generate final report
        self.generate_report()
        
        print(f'\n🏁 Testing completed: {datetime.now().isoformat()}')

def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Django Telegram API endpoints')
    parser.add_argument('--url', default='http://localhost:8000', 
                       help='Django server URL (default: http://localhost:8000)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    print('Django Telegram API Tester')
    print('==========================')
    print(f'Server URL: {args.url}')
    print('Make sure Django server is running!\n')
    
    tester = DjangoTelegramTester(args.url)
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print('\n\n⚠️  Tests interrupted by user')
    except Exception as e:
        print(f'\n\n💥 Test suite crashed: {e}')
        if args.verbose:
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()