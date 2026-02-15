import requests
import sys
import json
from datetime import datetime, timedelta

class HRFlowAPITester:
    def __init__(self, base_url="https://emp-alerts.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.company_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data storage
        self.employee_id = None
        self.payroll_id = None
        self.attendance_id = None
        self.vacation_id = None
        self.evaluation_id = None
        self.job_id = None
        self.candidate_id = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, auth_required=True):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth_required and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f" (Expected: {expected_status})"
                if response.text:
                    try:
                        error_data = response.json()
                        details += f" - {error_data.get('detail', response.text[:100])}"
                    except:
                        details += f" - {response.text[:100]}"

            self.log_test(name, success, details)
            return success, response.json() if success and response.text else {}

        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, {}

    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n🔐 Testing Authentication Endpoints...")
        
        # Test user registration
        test_email = f"test_{datetime.now().strftime('%H%M%S')}@hrflow.com"
        register_data = {
            "email": test_email,
            "password": "Test123456",
            "name": "Test User",
            "company_name": "Test Company S.A."
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=register_data,
            auth_required=False
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['user_id']
            self.company_id = response['user']['company_id']
            print(f"   Token obtained: {self.token[:20]}...")
        
        # Test user login
        login_data = {
            "email": test_email,
            "password": "Test123456"
        }
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data=login_data,
            auth_required=False
        )
        
        # Test get current user
        self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )

    def test_subscription_endpoints(self):
        """Test subscription and plans endpoints"""
        print("\n💳 Testing Subscription Endpoints...")
        
        # Test get plans
        self.run_test(
            "Get Subscription Plans",
            "GET",
            "plans",
            200,
            auth_required=False
        )
        
        # Test get current subscription
        self.run_test(
            "Get Current Subscription",
            "GET",
            "subscription",
            200
        )

    def test_employee_endpoints(self):
        """Test employee CRUD operations"""
        print("\n👥 Testing Employee Endpoints...")
        
        # Test get employees (empty initially)
        self.run_test(
            "Get Employees List",
            "GET",
            "employees",
            200
        )
        
        # Test create employee
        employee_data = {
            "first_name": "Juan",
            "last_name": "Pérez",
            "email": "juan.perez@testcompany.com",
            "phone": "+52 55 1234 5678",
            "position": "Desarrollador Senior",
            "department": "TI",
            "hire_date": "2024-01-15",
            "salary": 50000.0,
            "status": "active"
        }
        
        success, response = self.run_test(
            "Create Employee",
            "POST",
            "employees",
            200,
            data=employee_data
        )
        
        if success and 'employee_id' in response:
            self.employee_id = response['employee_id']
            print(f"   Employee created: {self.employee_id}")
        
        # Test get specific employee
        if self.employee_id:
            self.run_test(
                "Get Specific Employee",
                "GET",
                f"employees/{self.employee_id}",
                200
            )
            
            # Test update employee
            updated_data = {**employee_data, "salary": 55000.0}
            self.run_test(
                "Update Employee",
                "PUT",
                f"employees/{self.employee_id}",
                200,
                data=updated_data
            )

    def test_payroll_endpoints(self):
        """Test payroll operations"""
        print("\n💰 Testing Payroll Endpoints...")
        
        if not self.employee_id:
            print("   Skipping payroll tests - no employee created")
            return
        
        # Test get payrolls
        self.run_test(
            "Get Payrolls List",
            "GET",
            "payroll",
            200
        )
        
        # Test create payroll
        payroll_data = {
            "employee_id": self.employee_id,
            "period_start": "2024-08-01",
            "period_end": "2024-08-31",
            "base_salary": 50000.0,
            "bonuses": 5000.0,
            "deductions": 2000.0
        }
        
        success, response = self.run_test(
            "Create Payroll",
            "POST",
            "payroll",
            200,
            data=payroll_data
        )
        
        if success and 'payroll_id' in response:
            self.payroll_id = response['payroll_id']
            print(f"   Payroll created: {self.payroll_id}")
            
            # Test approve payroll
            self.run_test(
                "Approve Payroll",
                "PUT",
                f"payroll/{self.payroll_id}/approve",
                200
            )
            
            # Test pay payroll
            self.run_test(
                "Pay Payroll",
                "PUT",
                f"payroll/{self.payroll_id}/pay",
                200
            )

    def test_attendance_endpoints(self):
        """Test attendance operations"""
        print("\n⏰ Testing Attendance Endpoints...")
        
        if not self.employee_id:
            print("   Skipping attendance tests - no employee created")
            return
        
        # Test get attendances
        self.run_test(
            "Get Attendances List",
            "GET",
            "attendance",
            200
        )
        
        # Test create attendance
        attendance_data = {
            "employee_id": self.employee_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "check_in": "09:00",
            "check_out": "17:00",
            "status": "present"
        }
        
        success, response = self.run_test(
            "Create Attendance",
            "POST",
            "attendance",
            200,
            data=attendance_data
        )
        
        if success and 'attendance_id' in response:
            self.attendance_id = response['attendance_id']
            print(f"   Attendance created: {self.attendance_id}")

    def test_vacation_endpoints(self):
        """Test vacation operations"""
        print("\n🏖️ Testing Vacation Endpoints...")
        
        if not self.employee_id:
            print("   Skipping vacation tests - no employee created")
            return
        
        # Test get vacations
        self.run_test(
            "Get Vacations List",
            "GET",
            "vacations",
            200
        )
        
        # Test create vacation
        start_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d")
        
        vacation_data = {
            "employee_id": self.employee_id,
            "start_date": start_date,
            "end_date": end_date,
            "vacation_type": "annual",
            "reason": "Vacaciones anuales"
        }
        
        success, response = self.run_test(
            "Create Vacation Request",
            "POST",
            "vacations",
            200,
            data=vacation_data
        )
        
        if success and 'vacation_id' in response:
            self.vacation_id = response['vacation_id']
            print(f"   Vacation created: {self.vacation_id}")
            
            # Test approve vacation
            self.run_test(
                "Approve Vacation",
                "PUT",
                f"vacations/{self.vacation_id}/approve",
                200
            )

    def test_evaluation_endpoints(self):
        """Test evaluation operations"""
        print("\n📊 Testing Evaluation Endpoints...")
        
        if not self.employee_id:
            print("   Skipping evaluation tests - no employee created")
            return
        
        # Test get evaluations
        self.run_test(
            "Get Evaluations List",
            "GET",
            "evaluations",
            200
        )
        
        # Test create evaluation
        evaluation_data = {
            "employee_id": self.employee_id,
            "evaluator_id": self.user_id,
            "period": "Q3-2024",
            "performance_score": 4.5,
            "goals_achieved": 4.0,
            "teamwork_score": 4.8,
            "communication_score": 4.2,
            "comments": "Excelente desempeño en el trimestre"
        }
        
        success, response = self.run_test(
            "Create Evaluation",
            "POST",
            "evaluations",
            200,
            data=evaluation_data
        )
        
        if success and 'evaluation_id' in response:
            self.evaluation_id = response['evaluation_id']
            print(f"   Evaluation created: {self.evaluation_id}")

    def test_recruitment_endpoints(self):
        """Test recruitment operations"""
        print("\n🎯 Testing Recruitment Endpoints...")
        
        # Test get jobs
        self.run_test(
            "Get Job Postings List",
            "GET",
            "jobs",
            200
        )
        
        # Test create job posting
        job_data = {
            "title": "Desarrollador Full Stack",
            "department": "TI",
            "description": "Buscamos desarrollador con experiencia en React y Python",
            "requirements": "3+ años de experiencia, React, Python, FastAPI",
            "salary_range": "$40,000 - $60,000 MXN",
            "location": "Ciudad de México",
            "employment_type": "full_time"
        }
        
        success, response = self.run_test(
            "Create Job Posting",
            "POST",
            "jobs",
            200,
            data=job_data
        )
        
        if success and 'job_id' in response:
            self.job_id = response['job_id']
            print(f"   Job created: {self.job_id}")
            
            # Test get candidates
            self.run_test(
                "Get Candidates List",
                "GET",
                "candidates",
                200
            )
            
            # Test create candidate
            candidate_data = {
                "job_id": self.job_id,
                "name": "María González",
                "email": "maria.gonzalez@email.com",
                "phone": "+52 55 9876 5432",
                "resume_url": "https://example.com/resume.pdf",
                "cover_letter": "Estoy muy interesada en esta posición..."
            }
            
            success, response = self.run_test(
                "Create Candidate",
                "POST",
                "candidates",
                200,
                data=candidate_data
            )
            
            if success and 'candidate_id' in response:
                self.candidate_id = response['candidate_id']
                print(f"   Candidate created: {self.candidate_id}")

    def test_dashboard_endpoints(self):
        """Test dashboard and reports"""
        print("\n📈 Testing Dashboard & Reports...")
        
        # Test dashboard stats
        self.run_test(
            "Get Dashboard Stats",
            "GET",
            "dashboard/stats",
            200
        )
        
        # Test payroll report
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        self.run_test(
            "Get Payroll Report",
            "GET",
            f"reports/payroll?year={current_year}&month={current_month}",
            200
        )
        
        # Test attendance report
        self.run_test(
            "Get Attendance Report",
            "GET",
            f"reports/attendance?year={current_year}&month={current_month}",
            200
        )

    def test_company_endpoints(self):
        """Test company operations"""
        print("\n🏢 Testing Company Endpoints...")
        
        # Test get company
        self.run_test(
            "Get Company Info",
            "GET",
            "company",
            200
        )
        
        # Test update company
        company_data = {
            "name": "Test Company S.A. Updated",
            "industry": "Tecnología",
            "address": "Av. Reforma 123, CDMX",
            "phone": "+52 55 1234 5678"
        }
        
        self.run_test(
            "Update Company Info",
            "PUT",
            "company",
            200,
            data=company_data
        )

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete employee (this will cascade to related records)
        if self.employee_id:
            success, _ = self.run_test(
                "Delete Test Employee",
                "DELETE",
                f"employees/{self.employee_id}",
                200
            )

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting HRFlow API Tests...")
        print(f"Testing against: {self.base_url}")
        
        # Run tests in order
        self.test_auth_endpoints()
        
        if not self.token:
            print("❌ Authentication failed - stopping tests")
            return False
        
        self.test_subscription_endpoints()
        self.test_company_endpoints()
        self.test_employee_endpoints()
        self.test_payroll_endpoints()
        self.test_attendance_endpoints()
        self.test_vacation_endpoints()
        self.test_evaluation_endpoints()
        self.test_recruitment_endpoints()
        self.test_dashboard_endpoints()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = HRFlowAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/test_reports/backend_test_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_tests': tester.tests_run,
            'passed_tests': tester.tests_passed,
            'success_rate': (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
            'results': tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())