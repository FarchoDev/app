import requests
import sys
import json
from datetime import datetime

class ISTQBAPITester:
    def __init__(self, base_url="https://istqb-trainer-1.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None
        self.first_module_id = None

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
        # First create a user for login testing
        test_email = f"login_test_{datetime.now().strftime('%H%M%S')}@istqb.com"
        
        # Register user first
        register_success, register_response = self.run_test(
            "Register User for Login Test",
            "POST",
            "auth/register",
            200,
            data={
                "email": test_email,
                "password": "password123",
                "full_name": "Login Test User"
            }
        )
        
        if not register_success:
            print("   ❌ Failed to register user for login test")
            return False
        
        # Now test login with the registered user
        success, response = self.run_test(
            "User Login",
            "POST", 
            "auth/login",
            200,
            data={
                "email": test_email,
                "password": "password123"
            }
        )
        
        if success and 'access_token' in response:
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

    def test_get_specific_module(self):
        """Test getting specific module details"""
        if not self.first_module_id:
            print("❌ No module ID available for specific module test")
            return False
            
        success, response = self.run_test(
            f"Get Specific Module ({self.first_module_id[:8]}...)",
            "GET",
            f"modules/{self.first_module_id}",
            200
        )
        
        if success:
            expected_fields = ['id', 'title', 'description', 'content', 'sections', 'learning_objectives', 'key_concepts']
            missing_fields = [field for field in expected_fields if field not in response]
            
            if not missing_fields:
                print("   ✅ All expected fields present in module detail")
                print(f"   📚 Module: {response.get('title')}")
                print(f"   📚 Sections: {len(response.get('sections', []))}")
                print(f"   📚 Learning objectives: {len(response.get('learning_objectives', []))}")
                print(f"   📚 Key concepts: {len(response.get('key_concepts', []))}")
                
                # Store first section ID for section completion test
                sections = response.get('sections', [])
                if sections:
                    self.first_section_id = sections[0].get('id')
                    print(f"   📝 First section: {sections[0].get('title')}")
                
                return True
            else:
                print(f"   ❌ Missing fields in module detail: {missing_fields}")
                return False
        return False

    def test_mark_section_complete(self):
        """Test marking a specific section as completed"""
        if not self.token or not self.first_module_id or not hasattr(self, 'first_section_id'):
            print("❌ Missing required data for section completion test")
            return False
            
        success, response = self.run_test(
            f"Mark Section Complete",
            "POST",
            f"progress/{self.first_module_id}/section/{self.first_section_id}",
            200
        )
        
        if success:
            expected_keys = ['message', 'progress_percentage', 'sections_completed']
            if all(key in response for key in expected_keys):
                print(f"   ✅ Section marked complete:")
                print(f"      Progress: {response.get('progress_percentage')}%")
                print(f"      Sections completed: {response.get('sections_completed')}")
                return True
            else:
                print(f"   ❌ Missing expected keys in response")
                return False
        return False

    def test_update_module_progress(self):
        """Test updating general module progress"""
        if not self.token or not self.first_module_id:
            print("❌ Missing required data for module progress test")
            return False
            
        # Test updating progress with query parameters
        endpoint = f"progress/{self.first_module_id}?progress_percentage=75&time_spent=30"
        if hasattr(self, 'first_section_id'):
            endpoint += f"&section_id={self.first_section_id}"
            
        success, response = self.run_test(
            "Update Module Progress",
            "POST",
            endpoint,
            200
        )
        
        if success and 'message' in response:
            print(f"   ✅ Progress updated successfully")
            return True
        return False

    def test_progress_calculation_accuracy(self):
        """Test that progress calculations are accurate"""
        if not self.token:
            print("❌ No token available for progress calculation test")
            return False
            
        # Get current progress
        success, progress_response = self.run_test(
            "Get Progress for Calculation Check",
            "GET",
            "progress",
            200
        )
        
        if not success:
            return False
            
        # Get dashboard stats
        success, stats_response = self.run_test(
            "Get Dashboard Stats for Calculation Check",
            "GET",
            "dashboard/stats",
            200
        )
        
        if success:
            total_modules = stats_response.get('total_modules', 0)
            completed_modules = stats_response.get('completed_modules', 0)
            completion_percentage = stats_response.get('completion_percentage', 0)
            
            # Verify calculation
            expected_percentage = round((completed_modules / total_modules * 100) if total_modules > 0 else 0, 1)
            
            if abs(completion_percentage - expected_percentage) < 0.1:  # Allow small floating point differences
                print(f"   ✅ Progress calculation accurate:")
                print(f"      {completed_modules}/{total_modules} = {completion_percentage}%")
                return True
            else:
                print(f"   ❌ Progress calculation incorrect:")
                print(f"      Expected: {expected_percentage}%, Got: {completion_percentage}%")
                return False
        return False

    # ==================== QUIZ SYSTEM TESTS ====================
    
    def test_get_quizzes(self):
        """Test getting available quizzes"""
        success, response = self.run_test(
            "Get Available Quizzes",
            "GET",
            "quizzes",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   ✅ Found {len(response)} quizzes")
            if len(response) > 0:
                # Store first quiz for detailed testing
                self.first_quiz = response[0]
                self.first_quiz_id = self.first_quiz.get('id')
                print(f"   📝 First quiz: {self.first_quiz.get('title')}")
                print(f"   📝 Quiz type: {self.first_quiz.get('quiz_type')}")
                print(f"   📝 Questions: {len(self.first_quiz.get('question_ids', []))}")
                print(f"   📝 Time limit: {self.first_quiz.get('time_limit')} minutes")
                print(f"   📝 Passing score: {self.first_quiz.get('passing_score')}%")
                
                # Verify quiz structure
                expected_fields = ['id', 'title', 'description', 'quiz_type', 'question_ids', 'passing_score']
                missing_fields = [field for field in expected_fields if field not in self.first_quiz]
                
                if not missing_fields:
                    print("   ✅ All expected fields present in quiz")
                    return True
                else:
                    print(f"   ❌ Missing fields in quiz: {missing_fields}")
                    return False
            else:
                print("   ⚠️  No quizzes found - this might be expected if none are created")
                return True
        return False

    def test_get_specific_quiz(self):
        """Test getting specific quiz details"""
        if not hasattr(self, 'first_quiz_id') or not self.first_quiz_id:
            print("❌ No quiz ID available for specific quiz test")
            return False
            
        success, response = self.run_test(
            f"Get Specific Quiz ({self.first_quiz_id[:8]}...)",
            "GET",
            f"quizzes/{self.first_quiz_id}",
            200
        )
        
        if success:
            expected_fields = ['id', 'title', 'description', 'quiz_type', 'question_ids', 'passing_score']
            missing_fields = [field for field in expected_fields if field not in response]
            
            if not missing_fields:
                print("   ✅ All expected fields present in quiz detail")
                print(f"   📝 Quiz: {response.get('title')}")
                print(f"   📝 Type: {response.get('quiz_type')}")
                print(f"   📝 Questions: {len(response.get('question_ids', []))}")
                return True
            else:
                print(f"   ❌ Missing fields in quiz detail: {missing_fields}")
                return False
        return False

    def test_get_quiz_questions(self):
        """Test getting questions for a specific quiz"""
        if not hasattr(self, 'first_quiz_id') or not self.first_quiz_id:
            print("❌ No quiz ID available for quiz questions test")
            return False
            
        success, response = self.run_test(
            f"Get Quiz Questions ({self.first_quiz_id[:8]}...)",
            "GET",
            f"quizzes/{self.first_quiz_id}/questions",
            200
        )
        
        if success:
            if 'quiz' in response and 'questions' in response:
                quiz_data = response['quiz']
                questions = response['questions']
                
                print(f"   ✅ Quiz questions retrieved:")
                print(f"      Quiz: {quiz_data.get('title')}")
                print(f"      Questions: {len(questions)}")
                
                if len(questions) > 0:
                    # Store questions for quiz attempt
                    self.quiz_questions = questions
                    
                    # Verify question structure (should not have correct answers exposed)
                    first_question = questions[0]
                    print(f"      First question: {first_question.get('question_text', '')[:50]}...")
                    print(f"      Options: {len(first_question.get('options', []))}")
                    
                    # Check that correct answers are not exposed
                    for option in first_question.get('options', []):
                        if 'is_correct' in option:
                            print(f"   ❌ Correct answers exposed in quiz questions!")
                            return False
                    
                    print("   ✅ Correct answers properly hidden from quiz questions")
                    return True
                else:
                    print("   ❌ No questions found in quiz")
                    return False
            else:
                print("   ❌ Invalid response structure for quiz questions")
                return False
        return False

    def test_start_quiz_attempt(self):
        """Test starting a new quiz attempt"""
        if not self.token or not hasattr(self, 'first_quiz_id') or not self.first_quiz_id:
            print("❌ Missing required data for quiz attempt test")
            return False
            
        success, response = self.run_test(
            f"Start Quiz Attempt",
            "POST",
            f"quizzes/{self.first_quiz_id}/attempt",
            200
        )
        
        if success:
            if 'attempt_id' in response and 'started_at' in response:
                self.attempt_id = response['attempt_id']
                print(f"   ✅ Quiz attempt started:")
                print(f"      Attempt ID: {self.attempt_id}")
                print(f"      Started at: {response['started_at']}")
                return True
            else:
                print("   ❌ Missing expected fields in quiz attempt response")
                return False
        return False

    def test_submit_quiz(self):
        """Test submitting quiz answers and getting results"""
        if not self.token or not hasattr(self, 'first_quiz_id') or not hasattr(self, 'quiz_questions'):
            print("❌ Missing required data for quiz submission test")
            return False
            
        # Prepare answers - simulate answering questions
        answers = []
        for question in self.quiz_questions:
            question_id = question.get('id')
            options = question.get('options', [])
            if options:
                # Select first option for each question (simple simulation)
                selected_option_id = options[0].get('id')
                answers.append({
                    "question_id": question_id,
                    "selected_option_id": selected_option_id
                })
        
        submission_data = {
            "quiz_id": self.first_quiz_id,
            "answers": answers,
            "time_taken": 300  # 5 minutes in seconds
        }
        
        success, response = self.run_test(
            f"Submit Quiz Answers",
            "POST",
            f"quizzes/{self.first_quiz_id}/submit",
            200,
            data=submission_data
        )
        
        if success:
            expected_fields = ['attempt_id', 'score', 'passed', 'correct_answers', 'total_questions', 'passing_score']
            missing_fields = [field for field in expected_fields if field not in response]
            
            if not missing_fields:
                print(f"   ✅ Quiz submitted successfully:")
                print(f"      Score: {response.get('score')}%")
                print(f"      Passed: {response.get('passed')}")
                print(f"      Correct: {response.get('correct_answers')}/{response.get('total_questions')}")
                print(f"      Passing score: {response.get('passing_score')}%")
                print(f"      Time taken: {response.get('time_taken')} seconds")
                
                # Verify score calculation
                correct = response.get('correct_answers', 0)
                total = response.get('total_questions', 1)
                expected_score = round((correct / total * 100)) if total > 0 else 0
                actual_score = response.get('score', 0)
                
                if actual_score == expected_score:
                    print("   ✅ Score calculation is correct")
                else:
                    print(f"   ❌ Score calculation incorrect: expected {expected_score}%, got {actual_score}%")
                    return False
                
                # Store attempt ID for history testing
                self.completed_attempt_id = response.get('attempt_id')
                return True
            else:
                print(f"   ❌ Missing fields in quiz submission response: {missing_fields}")
                return False
        return False

    def test_get_quiz_attempts_history(self):
        """Test getting user's quiz attempt history"""
        if not self.token:
            print("❌ No token available for quiz attempts history test")
            return False
            
        success, response = self.run_test(
            "Get Quiz Attempts History",
            "GET",
            "quiz-attempts",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   ✅ Quiz attempts history retrieved: {len(response)} attempts")
            
            if len(response) > 0:
                # Verify attempt structure
                first_attempt = response[0]
                expected_fields = ['id', 'user_id', 'quiz_id', 'score', 'passed', 'started_at', 'quiz_title']
                missing_fields = [field for field in expected_fields if field not in first_attempt]
                
                if not missing_fields:
                    print("   ✅ All expected fields present in attempt history")
                    print(f"      Latest attempt: {first_attempt.get('quiz_title')}")
                    print(f"      Score: {first_attempt.get('score')}%")
                    print(f"      Status: {'Passed' if first_attempt.get('passed') else 'Failed'}")
                    return True
                else:
                    print(f"   ❌ Missing fields in attempt history: {missing_fields}")
                    return False
            else:
                print("   ⚠️  No quiz attempts found in history")
                return True
        return False

    def test_get_specific_quiz_attempt(self):
        """Test getting detailed results of a specific quiz attempt"""
        if not self.token or not hasattr(self, 'completed_attempt_id'):
            print("❌ Missing required data for specific quiz attempt test")
            return False
            
        success, response = self.run_test(
            f"Get Specific Quiz Attempt Results",
            "GET",
            f"quiz-attempts/{self.completed_attempt_id}",
            200
        )
        
        if success:
            expected_fields = ['attempt', 'quiz', 'detailed_results']
            missing_fields = [field for field in expected_fields if field not in response]
            
            if not missing_fields:
                attempt = response['attempt']
                quiz = response['quiz']
                detailed_results = response['detailed_results']
                
                print(f"   ✅ Detailed quiz attempt results retrieved:")
                print(f"      Quiz: {quiz.get('title')}")
                print(f"      Score: {attempt.get('score')}%")
                print(f"      Questions analyzed: {len(detailed_results)}")
                
                # Verify detailed results structure
                if len(detailed_results) > 0:
                    first_result = detailed_results[0]
                    result_fields = ['question_id', 'question_text', 'selected_option_id', 'correct_option_id', 'is_correct', 'options', 'explanation']
                    missing_result_fields = [field for field in result_fields if field not in first_result]
                    
                    if not missing_result_fields:
                        print("   ✅ All expected fields present in detailed results")
                        correct_count = sum(1 for result in detailed_results if result.get('is_correct'))
                        print(f"      Correct answers: {correct_count}/{len(detailed_results)}")
                        return True
                    else:
                        print(f"   ❌ Missing fields in detailed results: {missing_result_fields}")
                        return False
                else:
                    print("   ❌ No detailed results found")
                    return False
            else:
                print(f"   ❌ Missing fields in quiz attempt response: {missing_fields}")
                return False
        return False

    def test_quiz_data_integrity(self):
        """Test that quiz data is properly linked to ISTQB modules"""
        if not hasattr(self, 'first_quiz') or not self.first_quiz:
            print("❌ No quiz data available for integrity test")
            return False
            
        quiz = self.first_quiz
        module_id = quiz.get('module_id')
        
        if module_id:
            # Verify the module exists
            success, module_response = self.run_test(
                f"Verify Quiz Module Link",
                "GET",
                f"modules/{module_id}",
                200
            )
            
            if success:
                print(f"   ✅ Quiz properly linked to module:")
                print(f"      Quiz: {quiz.get('title')}")
                print(f"      Module: {module_response.get('title')}")
                return True
            else:
                print(f"   ❌ Quiz linked to non-existent module: {module_id}")
                return False
        else:
            print("   ⚠️  Quiz not linked to specific module (general quiz)")
            return True

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
        ("Get Specific Module", tester.test_get_specific_module),
        ("Dashboard Stats", tester.test_dashboard_stats),
        ("User Progress", tester.test_user_progress),
        ("Mark Section Complete", tester.test_mark_section_complete),
        ("Update Module Progress", tester.test_update_module_progress),
        ("Progress Calculation Accuracy", tester.test_progress_calculation_accuracy),
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