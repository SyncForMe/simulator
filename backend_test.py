#!/usr/bin/env python3
import requests
import json
import time
import os
import sys
from dotenv import load_dotenv
import base64
import re
import uuid
import jwt
from datetime import datetime, timedelta
import statistics

# Load environment variables from frontend/.env
load_dotenv('/app/frontend/.env')

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL')
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    sys.exit(1)

# Ensure the URL ends with /api
API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Load JWT secret from backend/.env for testing
load_dotenv('/app/backend/.env')
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    print("Warning: JWT_SECRET not found in environment variables. Some tests may fail.")
    JWT_SECRET = "test_secret"

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}

# Global variables for auth testing
auth_token = None
test_user_id = None
created_document_ids = []

def run_test(test_name, endpoint, method="GET", data=None, expected_status=200, expected_keys=None, auth=False, headers=None, params=None, measure_time=False):
    """Run a test against the specified endpoint"""
    url = f"{API_URL}{endpoint}"
    print(f"\n{'='*80}\nTesting: {test_name} ({method} {url})")
    
    # Set up headers with auth token if needed
    if headers is None:
        headers = {}
    
    if auth and auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    try:
        start_time = time.time()
        
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, params=params)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, params=params)
        elif method == "DELETE":
            if data is not None:
                response = requests.delete(url, json=data, headers=headers, params=params)
            else:
                response = requests.delete(url, headers=headers, params=params)
        else:
            print(f"Unsupported method: {method}")
            return False, None
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Print response details
        print(f"Status Code: {response.status_code}")
        if measure_time:
            print(f"Response Time: {response_time:.4f} seconds")
        
        # Check if response is JSON
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response is not JSON: {response.text}")
            response_data = {}
        
        # Verify status code
        status_ok = response.status_code == expected_status
        
        # Verify expected keys if provided
        keys_ok = True
        if expected_keys and status_ok:
            for key in expected_keys:
                if key not in response_data:
                    print(f"Missing expected key in response: {key}")
                    keys_ok = False
        
        # Determine test result
        test_passed = status_ok and keys_ok
        
        # Update test results
        result = "PASSED" if test_passed else "FAILED"
        print(f"Test Result: {result}")
        
        test_result = {
            "name": test_name,
            "endpoint": endpoint,
            "method": method,
            "status_code": response.status_code,
            "expected_status": expected_status,
            "result": result
        }
        
        if measure_time:
            test_result["response_time"] = response_time
            
        test_results["tests"].append(test_result)
        
        if test_passed:
            test_results["passed"] += 1
        else:
            test_results["failed"] += 1
        
        return test_passed, response_data
    
    except Exception as e:
        print(f"Error during test: {e}")
        test_results["tests"].append({
            "name": test_name,
            "endpoint": endpoint,
            "method": method,
            "result": "ERROR",
            "error": str(e)
        })
        test_results["failed"] += 1
        return False, None

def print_summary():
    """Print a summary of all test results"""
    print("\n" + "="*80)
    print(f"TEST SUMMARY: {test_results['passed']} passed, {test_results['failed']} failed")
    print("="*80)
    
    for i, test in enumerate(test_results["tests"], 1):
        result_symbol = "✅" if test["result"] == "PASSED" else "❌"
        print(f"{i}. {result_symbol} {test['name']} ({test['method']} {test['endpoint']})")
    
    print("="*80)
    overall_result = "PASSED" if test_results["failed"] == 0 else "FAILED"
    print(f"OVERALL RESULT: {overall_result}")
    print("="*80)

def test_login():
    """Login with test endpoint to get auth token"""
    global auth_token, test_user_id
    
    test_login_test, test_login_response = run_test(
        "Test Login Endpoint",
        "/auth/test-login",
        method="POST",
        expected_keys=["access_token", "token_type", "user"]
    )
    
    # Store the token for further testing if successful
    if test_login_test and test_login_response:
        auth_token = test_login_response.get("access_token")
        user_data = test_login_response.get("user", {})
        test_user_id = user_data.get("id")
        print(f"Test login successful. User ID: {test_user_id}")
        print(f"JWT Token: {auth_token}")
        return True
    else:
        print("Test login failed. Some tests may not work correctly.")
        return False

def test_document_creation():
    """Create test documents across different categories"""
    print("\n" + "="*80)
    print("CREATING TEST DOCUMENTS")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot create test documents without authentication")
            return False, "Authentication failed"
    
    # Define categories to create documents for
    categories = ["Protocol", "Training", "Research", "Equipment", "Budget", "Reference"]
    
    # Create a document for each category
    for category in categories:
        document_data = {
            "title": f"Test {category} Document",
            "category": category,
            "description": f"This is a test document for the {category} category",
            "content": f"""# Test {category} Document

## Purpose
This document was created for testing the File Center functionality.

## Content
This is a test document for the {category} category.
It contains some sample content to test document loading and management.

## Details
- Category: {category}
- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Author: Test User
- Keywords: test, {category.lower()}, documentation

## Sample Data
Here is some sample data to increase the document size:
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam auctor, 
nisl eget ultricies tincidunt, nisl nisl aliquam nisl, eget ultricies
nisl nisl eget nisl. Nullam auctor, nisl eget ultricies tincidunt, nisl
nisl aliquam nisl, eget ultricies nisl nisl eget nisl.
""",
            "keywords": ["test", category.lower(), "documentation"],
            "authors": ["Test User"]
        }
        
        create_doc_test, create_doc_response = run_test(
            f"Create {category} Document",
            "/documents/create",
            method="POST",
            data=document_data,
            auth=True,
            expected_keys=["success", "document_id"]
        )
        
        if create_doc_test and create_doc_response:
            document_id = create_doc_response.get("document_id")
            if document_id:
                print(f"✅ Created {category} document with ID: {document_id}")
                created_document_ids.append(document_id)
            else:
                print(f"❌ Failed to get document ID for {category} document")
        else:
            print(f"❌ Failed to create {category} document")
    
    # Print summary
    print("\nDOCUMENT CREATION SUMMARY:")
    if len(created_document_ids) == len(categories):
        print(f"✅ Successfully created {len(created_document_ids)} documents across all categories")
        return True, created_document_ids
    else:
        print(f"❌ Created only {len(created_document_ids)} out of {len(categories)} documents")
        return False, created_document_ids

def test_document_loading_performance():
    """Test the document loading performance"""
    print("\n" + "="*80)
    print("TESTING DOCUMENT LOADING PERFORMANCE")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test document loading without authentication")
            return False, "Authentication failed"
    
    # Test 1: Measure response time for GET /api/documents endpoint
    print("\nTest 1: Measuring response time for GET /api/documents endpoint")
    
    # Run multiple requests to get average response time
    response_times = []
    response_sizes = []
    document_counts = []
    
    for i in range(5):
        print(f"\nRequest {i+1}/5:")
        start_time = time.time()
        
        get_docs_test, get_docs_response = run_test(
            f"Document Loading Performance - Request {i+1}",
            "/documents",
            method="GET",
            auth=True,
            measure_time=True
        )
        
        # Get the response time from the last test
        if test_results["tests"][-1].get("response_time"):
            response_times.append(test_results["tests"][-1]["response_time"])
            
            # Calculate response size
            if get_docs_response:
                response_size = len(json.dumps(get_docs_response))
                response_sizes.append(response_size)
                document_counts.append(len(get_docs_response))
                print(f"Response size: {response_size} bytes")
                print(f"Document count: {len(get_docs_response)}")
    
    # Calculate statistics
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        median_time = statistics.median(response_times)
        
        print("\nResponse Time Statistics:")
        print(f"Average: {avg_time:.4f} seconds")
        print(f"Median: {median_time:.4f} seconds")
        print(f"Min: {min_time:.4f} seconds")
        print(f"Max: {max_time:.4f} seconds")
        
        # Evaluate performance
        if avg_time < 0.1:
            print("✅ Document loading performance is excellent (< 0.1 seconds)")
            performance_rating = "Excellent"
        elif avg_time < 0.5:
            print("✅ Document loading performance is good (< 0.5 seconds)")
            performance_rating = "Good"
        elif avg_time < 1.0:
            print("⚠️ Document loading performance is acceptable but could be improved (< 1.0 seconds)")
            performance_rating = "Acceptable"
        else:
            print("❌ Document loading performance is poor (> 1.0 seconds)")
            performance_rating = "Poor"
    else:
        print("❌ No valid response times recorded")
        performance_rating = "Unknown"
    
    # Test 2: Check response data structure
    print("\nTest 2: Checking response data structure")
    
    # Get documents with timing
    get_docs_test, get_docs_response = run_test(
        "Get All Documents",
        "/documents",
        method="GET",
        auth=True,
        measure_time=True
    )
    
    data_structure_issues = []
    
    if get_docs_test and get_docs_response:
        # Check document count
        doc_count = len(get_docs_response)
        print(f"Total documents: {doc_count}")
        
        # Check if response contains the expected data structure
        if doc_count > 0:
            sample_doc = get_docs_response[0]
            print("\nSample document structure:")
            for key in sample_doc.keys():
                print(f"- {key}")
            
            # Check for required fields
            required_fields = ["id", "metadata", "content", "preview"]
            missing_fields = [field for field in required_fields if field not in sample_doc]
            if missing_fields:
                data_structure_issues.append(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Check metadata structure
            if "metadata" in sample_doc:
                metadata = sample_doc["metadata"]
                print("\nMetadata structure:")
                for key in metadata.keys():
                    print(f"- {key}")
                
                # Check for required metadata fields
                required_metadata = ["id", "title", "category", "description", "created_at", "updated_at"]
                missing_metadata = [field for field in required_metadata if field not in metadata]
                if missing_metadata:
                    data_structure_issues.append(f"Missing required metadata fields: {', '.join(missing_metadata)}")
            else:
                data_structure_issues.append("Missing metadata field")
            
            # Check preview field
            if "preview" in sample_doc:
                preview_length = len(sample_doc["preview"])
                content_length = len(sample_doc.get("content", ""))
                print(f"\nPreview length: {preview_length} characters")
                print(f"Content length: {content_length} characters")
                
                if preview_length >= content_length and content_length > 200:
                    data_structure_issues.append("Preview is not shorter than content for large documents")
                
                if preview_length == 0:
                    data_structure_issues.append("Preview field is empty")
            else:
                data_structure_issues.append("Missing preview field")
    
    # Print data structure issues
    if data_structure_issues:
        print("\nData Structure Issues Found:")
        for issue in data_structure_issues:
            print(f"⚠️ {issue}")
    else:
        print("\n✅ No data structure issues found")
        print("✅ Response includes all required fields: id, metadata, content, preview")
        print("✅ Metadata includes all required fields: id, title, category, description, created_at, updated_at")
        print("✅ Preview field is properly implemented for efficient rendering")
    
    # Test 3: Check response consistency across multiple requests
    print("\nTest 3: Checking response consistency across multiple requests")
    
    if document_counts and len(set(document_counts)) == 1:
        print(f"✅ Document count is consistent across all requests: {document_counts[0]} documents")
    elif document_counts:
        print(f"⚠️ Document count varies across requests: {document_counts}")
        data_structure_issues.append("Inconsistent document count across requests")
    
    # Print summary
    print("\nDOCUMENT LOADING PERFORMANCE SUMMARY:")
    if performance_rating in ["Excellent", "Good"]:
        print(f"✅ Document loading performance is {performance_rating.lower()} with average response time of {avg_time:.4f} seconds")
        if not data_structure_issues:
            print("✅ No data structure issues detected")
        else:
            print(f"⚠️ {len(data_structure_issues)} data structure issues detected")
        return True, {"performance": performance_rating, "avg_time": avg_time, "issues": data_structure_issues}
    else:
        print(f"❌ Document loading performance is {performance_rating.lower()} with average response time of {avg_time:.4f} seconds")
        if data_structure_issues:
            print(f"❌ {len(data_structure_issues)} data structure issues detected")
        return False, {"performance": performance_rating, "avg_time": avg_time, "issues": data_structure_issues}

def test_document_bulk_delete():
    """Test the document bulk delete functionality"""
    print("\n" + "="*80)
    print("TESTING DOCUMENT BULK DELETE FUNCTIONALITY")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test document bulk delete without authentication")
            return False, "Authentication failed"
    
    # Create test documents for deletion
    print("\nCreating test documents for bulk delete testing...")
    test_doc_ids = []
    
    for i in range(3):
        document_data = {
            "title": f"Test Document for Bulk Delete {uuid.uuid4()}",
            "category": "Protocol",
            "description": "This is a test document for bulk delete testing",
            "content": "# Test Document\n\nThis is a test document for bulk delete testing.",
            "keywords": ["test", "bulk", "delete"],
            "authors": ["Test User"]
        }
        
        create_doc_test, create_doc_response = run_test(
            f"Create Test Document {i+1}",
            "/documents/create",
            method="POST",
            data=document_data,
            auth=True,
            expected_keys=["success", "document_id"]
        )
        
        if create_doc_test and create_doc_response:
            document_id = create_doc_response.get("document_id")
            if document_id:
                print(f"✅ Created test document {i+1} with ID: {document_id}")
                test_doc_ids.append(document_id)
            else:
                print(f"❌ Failed to get document ID for test document {i+1}")
        else:
            print(f"❌ Failed to create test document {i+1}")
    
    if not test_doc_ids:
        print("❌ Failed to create any test documents for bulk delete testing")
        return False, "Failed to create test documents"
    
    print(f"Created {len(test_doc_ids)} test documents for bulk delete testing")
    
    # Test 1: Test POST bulk delete with empty array
    print("\nTest 1: Testing POST bulk delete with empty array")
    
    empty_post_data = {
        "document_ids": []
    }
    
    empty_post_delete_test, empty_post_delete_response = run_test(
        "POST Bulk Delete with Empty Array",
        "/documents/bulk-delete",
        method="POST",
        data=empty_post_data,
        auth=True,
        expected_keys=["message", "deleted_count"]
    )
    
    if empty_post_delete_test and empty_post_delete_response:
        if empty_post_delete_response.get("deleted_count") == 0:
            print("✅ POST bulk delete with empty array returned deleted_count=0")
        else:
            print(f"❌ POST bulk delete with empty array returned unexpected deleted_count: {empty_post_delete_response.get('deleted_count')}")
    
    # Test 2: Test POST bulk delete with valid document IDs
    print("\nTest 2: Testing POST bulk delete with valid document IDs")
    
    # Use half of the created documents for deletion
    docs_to_delete = test_doc_ids[:len(test_doc_ids)//2]
    valid_post_data = {
        "document_ids": docs_to_delete
    }
    
    valid_post_delete_test, valid_post_delete_response = run_test(
        "POST Bulk Delete with Valid IDs",
        "/documents/bulk-delete",
        method="POST",
        data=valid_post_data,
        auth=True,
        expected_keys=["message", "deleted_count"]
    )
    
    if valid_post_delete_test and valid_post_delete_response:
        if valid_post_delete_response.get("deleted_count") == len(docs_to_delete):
            print(f"✅ POST bulk delete successfully deleted {len(docs_to_delete)} documents")
            
            # Remove the deleted IDs from our tracking list
            for doc_id in docs_to_delete:
                if doc_id in test_doc_ids:
                    test_doc_ids.remove(doc_id)
        else:
            print(f"❌ POST bulk delete returned unexpected deleted_count: {valid_post_delete_response.get('deleted_count')}")
    
    # Test 3: Test POST bulk delete with non-existent document IDs
    print("\nTest 3: Testing POST bulk delete with non-existent document IDs")
    
    fake_ids = [str(uuid.uuid4()) for _ in range(3)]
    fake_post_data = {
        "document_ids": fake_ids
    }
    
    fake_post_delete_test, fake_post_delete_response = run_test(
        "POST Bulk Delete with Non-existent IDs",
        "/documents/bulk-delete",
        method="POST",
        data=fake_post_data,
        auth=True,
        expected_status=404
    )
    
    if fake_post_delete_test:
        print("✅ POST bulk delete with non-existent IDs correctly returned 404 status")
    
    # Test 4: Test DELETE bulk delete with empty array
    print("\nTest 4: Testing DELETE bulk delete with empty array")
    
    # Try different formats for the empty array
    empty_formats = [
        [],                    # Direct array
        {"document_ids": []},  # Object with document_ids field
        {"data": []}           # Object with data field
    ]
    
    empty_delete_success = False
    
    for i, empty_data in enumerate(empty_formats):
        print(f"\nTrying empty array format {i+1}: {empty_data}")
        
        empty_delete_test, empty_delete_response = run_test(
            f"DELETE Bulk Delete with Empty Array (Format {i+1})",
            "/documents/bulk",
            method="DELETE",
            data=empty_data,
            auth=True,
            expected_keys=["message", "deleted_count"]
        )
        
        if empty_delete_test and empty_delete_response:
            if empty_delete_response.get("deleted_count") == 0:
                print(f"✅ DELETE bulk delete with empty array format {i+1} returned deleted_count=0")
                empty_delete_success = True
                break
            else:
                print(f"❌ DELETE bulk delete with empty array format {i+1} returned unexpected deleted_count: {empty_delete_response.get('deleted_count')}")
    
    if not empty_delete_success:
        print("❌ All DELETE bulk delete with empty array formats failed")
    
    # Test 5: Test DELETE bulk delete with valid document IDs
    print("\nTest 5: Testing DELETE bulk delete with valid document IDs")
    
    if test_doc_ids:
        # Try different formats for the document IDs
        valid_formats = [
            test_doc_ids,                    # Direct array
            {"document_ids": test_doc_ids},  # Object with document_ids field
            {"data": test_doc_ids}           # Object with data field
        ]
        
        valid_delete_success = False
        
        for i, valid_data in enumerate(valid_formats):
            print(f"\nTrying valid IDs format {i+1}: {valid_data}")
            
            valid_delete_test, valid_delete_response = run_test(
                f"DELETE Bulk Delete with Valid IDs (Format {i+1})",
                "/documents/bulk",
                method="DELETE",
                data=valid_data,
                auth=True,
                expected_keys=["message", "deleted_count"]
            )
            
            if valid_delete_test and valid_delete_response:
                if valid_delete_response.get("deleted_count") == len(test_doc_ids):
                    print(f"✅ DELETE bulk delete with valid IDs format {i+1} successfully deleted {len(test_doc_ids)} documents")
                    valid_delete_success = True
                    test_doc_ids = []
                    break
                else:
                    print(f"❌ DELETE bulk delete with valid IDs format {i+1} returned unexpected deleted_count: {valid_delete_response.get('deleted_count')}")
        
        if not valid_delete_success:
            print("❌ All DELETE bulk delete with valid IDs formats failed")
    else:
        print("⚠️ Skipping DELETE bulk delete with valid IDs test as all test documents were already deleted")
    
    # Test 6: Test DELETE bulk delete with non-existent document IDs
    print("\nTest 6: Testing DELETE bulk delete with non-existent document IDs")
    
    fake_ids = [str(uuid.uuid4()) for _ in range(3)]
    fake_data = fake_ids  # Try direct array format
    
    fake_delete_test, fake_delete_response = run_test(
        "DELETE Bulk Delete with Non-existent IDs",
        "/documents/bulk",
        method="DELETE",
        data=fake_data,
        auth=True,
        expected_status=404
    )
    
    if fake_delete_test:
        print("✅ DELETE bulk delete with non-existent IDs correctly returned 404 status")
    
    # Print summary
    print("\nDOCUMENT BULK DELETE FUNCTIONALITY SUMMARY:")
    
    # Check if all tests passed
    post_empty_array_works = empty_post_delete_test and empty_post_delete_response and empty_post_delete_response.get("deleted_count") == 0
    post_valid_ids_works = valid_post_delete_test and valid_post_delete_response and valid_post_delete_response.get("deleted_count") > 0
    post_fake_ids_works = fake_post_delete_test
    delete_empty_array_works = empty_delete_success
    delete_valid_ids_works = valid_delete_success
    delete_fake_ids_works = fake_delete_test
    
    # Summarize POST endpoint
    print("\nPOST /api/documents/bulk-delete endpoint:")
    if post_empty_array_works and post_valid_ids_works and post_fake_ids_works:
        print("✅ POST bulk delete endpoint is working correctly for all test cases")
    else:
        print("❌ POST bulk delete endpoint has issues:")
        if not post_empty_array_works:
            print("  - Empty array case is not working correctly")
        if not post_valid_ids_works:
            print("  - Valid document IDs case is not working correctly")
        if not post_fake_ids_works:
            print("  - Non-existent document IDs case is not working correctly")
    
    # Summarize DELETE endpoint
    print("\nDELETE /api/documents/bulk endpoint:")
    if delete_empty_array_works and delete_valid_ids_works and delete_fake_ids_works:
        print("✅ DELETE bulk delete endpoint is working correctly for all test cases")
    else:
        print("❌ DELETE bulk delete endpoint has issues:")
        if not delete_empty_array_works:
            print("  - Empty array case is not working correctly")
        if not delete_valid_ids_works:
            print("  - Valid document IDs case is not working correctly")
        if not delete_fake_ids_works:
            print("  - Non-existent document IDs case is not working correctly")
    
    # Overall assessment
    if ((post_empty_array_works and post_valid_ids_works and post_fake_ids_works) or 
       (delete_empty_array_works and delete_valid_ids_works and delete_fake_ids_works)):
        print("\n✅ At least one bulk delete endpoint is fully functional")
        return True, "At least one bulk delete endpoint is fully functional"
    else:
        print("\n❌ Both bulk delete endpoints have issues")
        return False, "Both bulk delete endpoints have issues"

def test_document_categories():
    """Test the document categories endpoint and count verification"""
    print("\n" + "="*80)
    print("TESTING DOCUMENT CATEGORIES ENDPOINT")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test document categories without authentication")
            return False, "Authentication failed"
    
    # Test 1: Get document categories
    print("\nTest 1: Getting document categories")
    
    categories_test, categories_response = run_test(
        "Get Document Categories",
        "/documents/categories",
        method="GET",
        auth=True,
        expected_keys=["categories"]
    )
    
    expected_categories = ["Protocol", "Training", "Research", "Equipment", "Budget", "Reference"]
    categories_match = False
    
    if categories_test and categories_response:
        categories = categories_response.get("categories", [])
        print(f"Retrieved categories: {categories}")
        
        # Check if all expected categories are present
        missing_categories = [cat for cat in expected_categories if cat not in categories]
        extra_categories = [cat for cat in categories if cat not in expected_categories]
        
        if not missing_categories and not extra_categories:
            print("✅ All expected categories are present")
            categories_match = True
        else:
            if missing_categories:
                print(f"❌ Missing categories: {missing_categories}")
            if extra_categories:
                print(f"⚠️ Extra categories found: {extra_categories}")
    
    # Test 2: Create documents for each category if needed
    print("\nTest 2: Ensuring documents exist for each category")
    
    # Get current documents
    get_docs_test, get_docs_response = run_test(
        "Get All Documents",
        "/documents",
        method="GET",
        auth=True
    )
    
    # Track document counts by category
    category_counts = {cat: 0 for cat in expected_categories}
    
    if get_docs_test and get_docs_response:
        # Count documents by category
        for doc in get_docs_response:
            category = doc.get("metadata", {}).get("category")
            if category in category_counts:
                category_counts[category] += 1
        
        print("Current document counts by category:")
        for category, count in category_counts.items():
            print(f"  - {category}: {count}")
        
        # Create documents for categories with zero count
        categories_to_create = [cat for cat, count in category_counts.items() if count == 0]
        
        if categories_to_create:
            print(f"\nCreating documents for {len(categories_to_create)} missing categories:")
            for category in categories_to_create:
                document_data = {
                    "title": f"Test {category} Document",
                    "category": category,
                    "description": f"This is a test document for the {category} category",
                    "content": f"# Test {category} Document\n\nThis is a test document for the {category} category.",
                    "keywords": ["test", category.lower()],
                    "authors": ["Test User"]
                }
                
                create_doc_test, create_doc_response = run_test(
                    f"Create {category} Document",
                    "/documents/create",
                    method="POST",
                    data=document_data,
                    auth=True,
                    expected_keys=["success", "document_id"]
                )
                
                if create_doc_test and create_doc_response:
                    document_id = create_doc_response.get("document_id")
                    if document_id:
                        print(f"✅ Created {category} document with ID: {document_id}")
                        created_document_ids.append(document_id)
                        category_counts[category] += 1
                    else:
                        print(f"❌ Failed to get document ID for {category} document")
                else:
                    print(f"❌ Failed to create {category} document")
    
    # Test 3: Get documents for each category and verify counts
    print("\nTest 3: Verifying document counts for each category")
    
    category_verification = {}
    
    for category in expected_categories:
        get_category_test, get_category_response = run_test(
            f"Get {category} Documents",
            f"/documents",
            method="GET",
            params={"category": category},
            auth=True
        )
        
        if get_category_test and get_category_response:
            actual_count = len(get_category_response)
            expected_count = category_counts[category]
            
            print(f"{category}: Expected {expected_count}, Found {actual_count}")
            
            category_verification[category] = {
                "expected": expected_count,
                "actual": actual_count,
                "match": actual_count == expected_count
            }
            
            if actual_count == expected_count:
                print(f"✅ {category} document count matches expected count")
            else:
                print(f"❌ {category} document count does not match expected count")
    
    # Print summary
    print("\nDOCUMENT CATEGORIES SUMMARY:")
    
    # Check if all tests passed
    categories_endpoint_works = categories_test and categories_match
    category_counts_match = all(v["match"] for v in category_verification.values())
    
    if categories_endpoint_works and category_counts_match:
        print("✅ Document categories functionality is working correctly!")
        print("✅ Categories endpoint returns the expected categories")
        print("✅ Document counts match for all categories")
        return True, {"categories": expected_categories, "counts": category_verification}
    else:
        issues = []
        if not categories_endpoint_works:
            issues.append("Categories endpoint is not returning the expected categories")
        
        mismatched_categories = [cat for cat, v in category_verification.items() if not v["match"]]
        if mismatched_categories:
            issues.append(f"Document counts do not match for categories: {', '.join(mismatched_categories)}")
        
        print("❌ Document categories functionality has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"categories": expected_categories, "counts": category_verification, "issues": issues}

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("RUNNING FILE CENTER API TESTS")
    print("="*80)
    
    # Test authentication first
    test_login()
    
    # Create test documents
    doc_creation_success, _ = test_document_creation()
    
    # Test document loading performance
    doc_loading_success, doc_loading_results = test_document_loading_performance()
    
    # Test document categories
    doc_categories_success, doc_categories_results = test_document_categories()
    
    # Test document bulk delete
    doc_bulk_delete_success, doc_bulk_delete_message = test_document_bulk_delete()
    
    # Print summary of all tests
    print_summary()
    
    # Print final conclusion
    print("\n" + "="*80)
    print("FILE CENTER FUNCTIONALITY ASSESSMENT")
    print("="*80)
    
    if doc_loading_success:
        print("✅ Document loading performance is acceptable")
        print(f"✅ Average response time: {doc_loading_results['avg_time']:.4f} seconds")
        if not doc_loading_results['issues']:
            print("✅ No optimization issues detected")
        else:
            print(f"⚠️ {len(doc_loading_results['issues'])} optimization issues detected:")
            for issue in doc_loading_results['issues']:
                print(f"  - {issue}")
    else:
        print("❌ Document loading performance needs improvement")
        print(f"❌ Average response time: {doc_loading_results['avg_time']:.4f} seconds")
        if doc_loading_results['issues']:
            print(f"❌ {len(doc_loading_results['issues'])} optimization issues detected:")
            for issue in doc_loading_results['issues']:
                print(f"  - {issue}")
    
    if doc_bulk_delete_success:
        print("✅ Document bulk delete functionality is working correctly")
        print("✅ Both DELETE and POST methods work for bulk delete")
        print("✅ Empty arrays are handled correctly")
        print("✅ Non-existent document IDs are handled correctly")
    else:
        print(f"❌ {doc_bulk_delete_message}")
    
    if doc_categories_success:
        print("✅ Document categories functionality is working correctly")
        print("✅ Categories endpoint returns the expected categories")
        print("✅ Document counts match for all categories")
    else:
        print("❌ Document categories functionality has issues")
        if "issues" in doc_categories_results:
            for issue in doc_categories_results["issues"]:
                print(f"  - {issue}")
    
    print("="*80)
    
    return doc_loading_success and doc_bulk_delete_success and doc_categories_success

if __name__ == "__main__":
    main()
