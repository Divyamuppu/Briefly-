#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class BrieflyAPITester:
    def __init__(self, base_url="https://style-finder-108.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.project_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json() if response.content else {}
                    if response_data and isinstance(response_data, dict) and len(str(response_data)) < 200:
                        print(f"   Response preview: {response_data}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_content = response.text[:200] if response.text else "No content"
                    print(f"   Error: {error_content}")
                except:
                    print(f"   Error: Could not read response")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_project_creation(self):
        """Test creating a new project"""
        project_data = {
            "project_name": f"Test Project {datetime.now().strftime('%H%M%S')}",
            "video_length": "30s",
            "platform": "Instagram", 
            "target_audience": "Young professionals aged 25-35",
            "brand_tones": {
                "fun_serious": 75,
                "luxury_casual": 40,
                "corporate_playful": 60
            }
        }
        
        success, response = self.run_test(
            "Create Project",
            "POST",
            "projects",
            200,
            data=project_data
        )
        
        if success and 'id' in response:
            self.project_id = response['id']
            print(f"   Project ID: {self.project_id}")
            return True
        return False

    def test_project_retrieval(self):
        """Test retrieving a project by ID"""
        if not self.project_id:
            print("❌ Cannot test project retrieval - no project ID")
            return False
            
        success, response = self.run_test(
            "Get Project",
            "GET",
            f"projects/{self.project_id}",
            200
        )
        return success

    def test_get_cards(self):
        """Test fetching swipe cards"""
        success, response = self.run_test(
            "Get Swipe Cards",
            "GET",
            "cards",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Retrieved {len(response)} cards")
            if len(response) > 0:
                print(f"   First card: {response[0].get('title', 'No title')}")
            return True
        return False

    def test_save_swipe(self):
        """Test saving a swipe action"""
        if not self.project_id:
            print("❌ Cannot test swipe saving - no project ID")
            return False
            
        swipe_data = {
            "project_id": self.project_id,
            "card_id": "editing_style_fast_paced_social_cuts",
            "action": "like"
        }
        
        success, response = self.run_test(
            "Save Swipe Action",
            "POST",
            "swipes",
            200,
            data=swipe_data
        )
        return success

    def test_get_brief(self):
        """Test generating and retrieving brief"""
        if not self.project_id:
            print("❌ Cannot test brief generation - no project ID")
            return False
            
        success, response = self.run_test(
            "Generate Brief",
            "GET",
            f"brief/{self.project_id}",
            200
        )
        
        if success:
            required_fields = ['project_id', 'project_name', 'editing_style', 'color_direction', 'music_direction', 'typography_direction', 'total_swipes']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Brief missing field: {field}")
                    return False
            print(f"   Brief generated with {response.get('total_swipes', 0)} swipes")
            return True
        return False

    def test_pdf_export(self):
        """Test PDF export functionality"""
        if not self.project_id:
            print("❌ Cannot test PDF export - no project ID")
            return False
            
        url = f"{self.api_url}/brief/{self.project_id}/pdf"
        print(f"\n🔍 Testing PDF Export...")
        print(f"   URL: {url}")
        
        self.tests_run += 1
        
        try:
            response = requests.get(url)
            success = response.status_code == 200 and response.headers.get('content-type') == 'application/pdf'
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - PDF generated, size: {len(response.content)} bytes")
                return True
            else:
                print(f"❌ Failed - Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}")
                return False
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🚀 Starting Briefly API Tests")
        print("=" * 50)
        
        # Test basic endpoints
        print("\n📋 BASIC API TESTS")
        print("-" * 30)
        
        # Test project creation first (needed for other tests)
        self.test_project_creation()
        
        # Test project retrieval
        self.test_project_retrieval()
        
        # Test cards endpoint
        self.test_get_cards()
        
        # Test swipe functionality
        self.test_save_swipe()
        
        # Add more swipes for better brief generation
        print("\n📊 ADDING MORE SWIPE DATA")
        print("-" * 30)
        additional_swipes = [
            {"card_id": "color_grading_warm_cinematic_tones", "action": "love"},
            {"card_id": "music_style_indie_electronic", "action": "like"},
            {"card_id": "typography_modern_geometric_sans", "action": "love"},
            {"card_id": "editing_style_cinematic_slow_pacing", "action": "dislike"},
            {"card_id": "color_grading_neon_cyberpunk", "action": "like"}
        ]
        
        for swipe in additional_swipes:
            swipe["project_id"] = self.project_id
            self.run_test(
                f"Save Swipe: {swipe['action']}",
                "POST", 
                "swipes",
                200,
                data=swipe
            )
        
        # Test brief generation
        print("\n📄 BRIEF GENERATION TESTS")
        print("-" * 30)
        self.test_get_brief()
        
        # Test PDF export
        self.test_pdf_export()
        
        # Print results
        print("\n" + "=" * 50)
        print(f"📊 FINAL RESULTS")
        print(f"Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.project_id:
            print(f"\n🔗 Test Project ID: {self.project_id}")
            print(f"Frontend URL: https://style-finder-108.preview.emergentagent.com/brief/{self.project_id}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main function"""
    tester = BrieflyAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())