import requests
import sys
import json
from datetime import datetime

class ISTQBAPITester:
    def __init__(self, base_url="https://istqbprep.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)

            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Expected {expected_status}, got {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except requests.exceptions.RequestException as e:
            print(f"❌ FAILED - Network Error: {str(e)}")
            return False, {}
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            return False, {}

    def test_user_registration(self):
        """Test user registration"""
        test_email = f"test_{datetime.now().strftime('%H%M%S')}@istqb.com"
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={
                "email": test_email,
                "password": "password123",
                "full_name": "Juan Testing"
            }
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response.get('user', {}).get('id')
            print(f"   ✅ Token obtained: {self.token[:20]}...")
            print(f"   ✅ User ID: {self.user_id}")
            return True
        return False

    def test_user_login(self):
        """Test user login with existing credentials"""
        success, response = self.run_test(
            "User Login",
            "POST", 
            "auth/login",
            200,
            data={
                "email": "test@istqb.com",
                "password": "password123"
            }
        )
        
        if success and 'access_token' in response:
            # Don't overwrite token from registration test
            print(f"   ✅ Login successful, token available")
            return True
        return False

    def test_protected_endpoint(self):
        """Test protected /auth/me endpoint"""
        if not self.token:
            print("❌ No token available for protected endpoint test")
            return False
            
        success, response = self.run_test(
            "Protected Endpoint (/auth/me)",
            "GET",
            "auth/me",
            200
        )
        
        if success and 'email' in response:
            print(f"   ✅ User data retrieved: {response.get('full_name')}")
            return True
        return False

    def test_get_modules(self):
        """Test getting ISTQB modules with expanded content"""
        success, response = self.run_test(
            "Get ISTQB Modules",
            "GET",
            "modules",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   ✅ Found {len(response)} modules")
            if len(response) >= 6:
                print("   ✅ Expected 6 modules found")
                
                # Verify expanded content structure
                first_module = response[0] if response else {}
                expected_fields = ['id', 'title', 'description', 'content', 'sections', 'learning_objectives', 'key_concepts', 'estimated_time']
                missing_fields = [field for field in expected_fields if field not in first_module]
                
                if not missing_fields:
                    print("   ✅ All expected fields present in modules")
                    print(f"   📚 First module has {len(first_module.get('sections', []))} sections")
                    print(f"   📚 First module has {len(first_module.get('learning_objectives', []))} learning objectives")
                    print(f"   📚 First module has {len(first_module.get('key_concepts', []))} key concepts")
                else:
                    print(f"   ❌ Missing fields in module: {missing_fields}")
                    return False
                
                # Store first module ID for detailed testing
                self.first_module_id = first_module.get('id')
                
                # Print module titles
                for i, module in enumerate(response[:3]):
                    print(f"   📚 Module {i+1}: {module.get('title', 'No title')}")
                if len(response) > 3:
                    print(f"   📚 ... and {len(response)-3} more modules")
                return True
            else:
                print(f"   ⚠️  Expected 6 modules, found {len(response)}")
                return False
        return False

    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint"""
        if not self.token:
            print("❌ No token available for dashboard stats test")
            return False
            
        success, response = self.run_test(
            "Dashboard Statistics",
            "GET",
            "dashboard/stats",
            200
        )
        
        if success:
            expected_keys = ['total_modules', 'completed_modules', 'total_time_spent', 'completion_percentage']
            if all(key in response for key in expected_keys):
                print(f"   ✅ Stats retrieved:")
                print(f"      Total modules: {response.get('total_modules')}")
                print(f"      Completed: {response.get('completed_modules')}")
                print(f"      Time spent: {response.get('total_time_spent')} minutes")
                print(f"      Progress: {response.get('completion_percentage')}%")
                return True
            else:
                print(f"   ❌ Missing expected keys in response")
                return False
        return False

    def test_user_progress(self):
        """Test user progress endpoint"""
        if not self.token:
            print("❌ No token available for user progress test")
            return False
            
        success, response = self.run_test(
            "User Progress",
            "GET",
            "progress",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   ✅ Progress data retrieved: {len(response)} entries")
            return True
        return False

def main():
    print("🚀 Starting ISTQB Platform API Tests")
    print("=" * 50)
    
    # Setup
    tester = ISTQBAPITester()
    
    # Test sequence
    tests = [
        ("User Registration", tester.test_user_registration),
        ("User Login", tester.test_user_login),
        ("Protected Endpoint", tester.test_protected_endpoint),
        ("Get Modules", tester.test_get_modules),
        ("Dashboard Stats", tester.test_dashboard_stats),
        ("User Progress", tester.test_user_progress),
    ]
    
    print(f"\n📋 Running {len(tests)} test categories...")
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {str(e)}")
    
    # Print final results
    print(f"\n{'='*50}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*50}")
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "0%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())