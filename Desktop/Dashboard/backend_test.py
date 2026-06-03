#!/usr/bin/env python3
"""
Backend API Testing for Rebalance Global Observatory
Tests all API endpoints including health, countries, and news functionality
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

class RebalanceAPITester:
    def __init__(self, base_url="https://geopolitics-index.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def test_health_endpoint(self) -> bool:
        """Test /api/health endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy" and "timestamp" in data:
                    self.log_test("Health Check", True, "API is healthy")
                    return True
                else:
                    self.log_test("Health Check", False, f"Invalid response format: {data}")
                    return False
            else:
                self.log_test("Health Check", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Health Check", False, f"Request failed: {str(e)}")
            return False

    def test_countries_endpoint(self) -> bool:
        """Test /api/countries endpoint"""
        try:
            response = requests.get(f"{self.api_url}/countries", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "countries" not in data:
                    self.log_test("Countries List", False, "Missing 'countries' field")
                    return False
                
                countries = data["countries"]
                if not isinstance(countries, list) or len(countries) == 0:
                    self.log_test("Countries List", False, "Countries list is empty or invalid")
                    return False
                
                # Check first country structure
                first_country = countries[0]
                required_fields = ["code", "name", "flag"]
                for field in required_fields:
                    if field not in first_country:
                        self.log_test("Countries List", False, f"Missing field '{field}' in country data")
                        return False
                
                self.log_test("Countries List", True, f"Found {len(countries)} countries")
                return True
            else:
                self.log_test("Countries List", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Countries List", False, f"Request failed: {str(e)}")
            return False

    def test_country_info_endpoint(self) -> bool:
        """Test /api/country/{country_code} endpoint"""
        test_countries = ["us", "gb", "de", "fr", "jp"]
        
        for country_code in test_countries:
            try:
                response = requests.get(f"{self.api_url}/country/{country_code}", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["code", "name", "flag", "newsapi_supported"]
                    
                    for field in required_fields:
                        if field not in data:
                            self.log_test(f"Country Info ({country_code})", False, f"Missing field '{field}'")
                            return False
                    
                    self.log_test(f"Country Info ({country_code})", True, f"Country: {data['name']}")
                else:
                    self.log_test(f"Country Info ({country_code})", False, f"Status code: {response.status_code}")
                    return False
                    
            except Exception as e:
                self.log_test(f"Country Info ({country_code})", False, f"Request failed: {str(e)}")
                return False
        
        return True

    def test_news_endpoint(self) -> bool:
        """Test /api/news/{country_code} endpoint"""
        test_countries = ["us", "gb", "de", "fr", "jp"]
        
        for country_code in test_countries:
            try:
                response = requests.get(f"{self.api_url}/news/{country_code}", timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check response structure
                    required_fields = ["status", "total_results", "articles", "country_name", "country_flag"]
                    for field in required_fields:
                        if field not in data:
                            self.log_test(f"News ({country_code})", False, f"Missing field '{field}'")
                            return False
                    
                    # Check articles structure
                    articles = data["articles"]
                    if not isinstance(articles, list):
                        self.log_test(f"News ({country_code})", False, "Articles is not a list")
                        return False
                    
                    if len(articles) > 0:
                        # Check first article structure
                        first_article = articles[0]
                        article_fields = ["source", "title", "url", "publishedAt"]
                        for field in article_fields:
                            if field not in first_article:
                                self.log_test(f"News ({country_code})", False, f"Missing article field '{field}'")
                                return False
                        
                        # Check source structure
                        if "name" not in first_article["source"]:
                            self.log_test(f"News ({country_code})", False, "Missing source name")
                            return False
                    
                    self.log_test(f"News ({country_code})", True, f"Found {len(articles)} articles for {data['country_name']}")
                else:
                    self.log_test(f"News ({country_code})", False, f"Status code: {response.status_code}")
                    return False
                    
            except Exception as e:
                self.log_test(f"News ({country_code})", False, f"Request failed: {str(e)}")
                return False
        
        return True

    def test_news_with_parameters(self) -> bool:
        """Test news endpoint with query parameters"""
        try:
            # Test with page_size parameter
            response = requests.get(f"{self.api_url}/news/us", params={"page_size": 5}, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                
                if len(articles) <= 5:  # Should respect page_size limit
                    self.log_test("News with Parameters", True, f"Page size parameter working: {len(articles)} articles")
                    return True
                else:
                    self.log_test("News with Parameters", False, f"Page size not respected: got {len(articles)} articles")
                    return False
            else:
                self.log_test("News with Parameters", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("News with Parameters", False, f"Request failed: {str(e)}")
            return False

    def test_invalid_endpoints(self) -> bool:
        """Test error handling for invalid requests"""
        test_cases = [
            ("/api/country/invalid", 404, "Invalid country code"),
            ("/api/news/invalid", 200, "Invalid country code (should return mock data)"),  # Mock data expected
        ]
        
        for endpoint, expected_status, description in test_cases:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                
                if response.status_code == expected_status:
                    self.log_test(f"Error Handling - {description}", True, f"Correct status: {response.status_code}")
                else:
                    # For news endpoint, mock data might be returned with 200 status
                    if endpoint.startswith("/api/news/") and response.status_code == 200:
                        self.log_test(f"Error Handling - {description}", True, "Mock data returned for invalid country")
                    else:
                        self.log_test(f"Error Handling - {description}", False, f"Expected {expected_status}, got {response.status_code}")
                        return False
                        
            except Exception as e:
                self.log_test(f"Error Handling - {description}", False, f"Request failed: {str(e)}")
                return False
        
        return True

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all backend tests"""
        print("🚀 Starting Backend API Tests for Rebalance Global Observatory")
        print(f"📍 Testing API at: {self.api_url}")
        print("=" * 60)
        
        # Run all tests
        tests = [
            self.test_health_endpoint,
            self.test_countries_endpoint,
            self.test_country_info_endpoint,
            self.test_news_endpoint,
            self.test_news_with_parameters,
            self.test_invalid_endpoints,
        ]
        
        for test in tests:
            test()
            print()  # Add spacing between tests
        
        # Print summary
        print("=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"✨ Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! Backend API is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": success_rate,
            "all_passed": self.tests_passed == self.tests_run,
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = RebalanceAPITester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results["all_passed"] else 1

if __name__ == "__main__":
    sys.exit(main())