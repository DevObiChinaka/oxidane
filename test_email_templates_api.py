"""
Test Email Templates API endpoints
"""

import requests
import json

# API Base URL
BASE_URL = "http://localhost:8000/api/users"

# Admin credentials (you'll need to get a valid admin token)
ADMIN_TOKEN = "your_admin_token_here"
HEADERS = {
    "Authorization": f"Bearer {ADMIN_TOKEN}",
    "Content-Type": "application/json"
}

def test_get_templates():
    """Test getting list of email templates"""
    print("🧪 Testing GET /admin/email-templates/")
    
    response = requests.get(f"{BASE_URL}/admin/email-templates/", headers=HEADERS)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Found {len(data.get('templates', []))} templates")
        
        for template in data.get('templates', [])[:3]:  # Show first 3
            print(f"   - {template['name']} ({template['template_type']})")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

def test_get_template_types():
    """Test getting available template types"""
    print("\n🧪 Testing GET /admin/email-template-types/")
    
    response = requests.get(f"{BASE_URL}/admin/email-template-types/", headers=HEADERS)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Found {len(data.get('types', []))} template types")
        
        for template_type in data.get('types', [])[:3]:  # Show first 3
            print(f"   - {template_type['label']} ({template_type['value']})")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

def test_email_analytics():
    """Test email analytics endpoint"""
    print("\n🧪 Testing GET /admin/email-analytics/")
    
    response = requests.get(f"{BASE_URL}/admin/email-analytics/", headers=HEADERS)
    
    if response.status_code == 200:
        data = response.json()
        analytics = data.get('analytics', {})
        print(f"✅ Success! Analytics data:")
        print(f"   - Total Templates: {analytics.get('total_templates', 0)}")
        print(f"   - Active Templates: {analytics.get('active_templates', 0)}")
        print(f"   - Total Sent: {analytics.get('total_sent', 0)}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

def test_create_template():
    """Test creating a new email template"""
    print("\n🧪 Testing POST /admin/email-templates/")
    
    template_data = {
        "name": "Test Template",
        "template_type": "custom",
        "subject_template": "Test Subject - {{user.first_name}}",
        "html_content": "<h1>Hello {{user.first_name}}!</h1><p>This is a test template from {{company_name}}.</p>",
        "description": "Test template created by API test",
        "status": "draft"
    }
    
    response = requests.post(
        f"{BASE_URL}/admin/email-templates/", 
        headers=HEADERS,
        data=json.dumps(template_data)
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Created template: {data.get('template', {}).get('name')}")
        return data.get('template', {}).get('id')
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_preview_template(template_id):
    """Test email template preview"""
    if not template_id:
        print("\n⏭️ Skipping preview test (no template ID)")
        return
        
    print(f"\n🧪 Testing POST /admin/email-templates/{template_id}/preview/")
    
    preview_data = {
        "sample_data": {
            "user": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com"
            }
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/admin/email-templates/{template_id}/preview/",
        headers=HEADERS,
        data=json.dumps(preview_data)
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Preview generated:")
        print(f"   - Subject: {data.get('subject', '')[:50]}...")
        print(f"   - Content Length: {len(data.get('html_content', ''))} chars")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("🚀 Email Templates API Test Suite")
    print("=" * 50)
    
    print("⚠️  Note: Make sure to:")
    print("   1. Start Django server: python manage.py runserver 8000")
    print("   2. Get admin token and update ADMIN_TOKEN variable")
    print("   3. Ensure you have admin permissions")
    print()
    
    # Run tests (uncomment when you have a valid admin token)
    # test_get_templates()
    # test_get_template_types()
    # test_email_analytics()
    # template_id = test_create_template()
    # test_preview_template(template_id)
    
    print("\n✅ Test suite ready! Update ADMIN_TOKEN and uncomment tests to run.")