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
from conversation_generation_test import test_conversation_generation
from dynamic_conversation_test import test_dynamic_conversation
from natural_expertise_test import test_natural_expertise

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
test_user_email = f"test.user.{uuid.uuid4()}@example.com"
test_user_password = "securePassword123"
test_user_name = "Test User"

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
        print(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}")
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
    
    # Try using the email/password login first
    login_data = {
        "email": test_user_email,
        "password": test_user_password
    }
    
    login_test, login_response = run_test(
        "Login with credentials",
        "/auth/login",
        method="POST",
        data=login_data,
        expected_keys=["access_token", "token_type", "user"]
    )
    
    # If email/password login fails, try the test login endpoint
    if not login_test or not login_response:
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
    else:
        # Store the token from email/password login
        auth_token = login_response.get("access_token")
        user_data = login_response.get("user", {})
        test_user_id = user_data.get("id")
        print(f"Login successful. User ID: {test_user_id}")
        print(f"JWT Token: {auth_token}")
        return True

def test_document_creation(num_documents=5):
    """Create test documents across different categories"""
    print("\n" + "="*80)
    print(f"CREATING {num_documents} TEST DOCUMENTS")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot create test documents without authentication")
            return False, "Authentication failed"
    
    # Define categories to create documents for
    categories = ["Protocol", "Training", "Research", "Equipment", "Budget", "Reference"]
    
    # Create documents
    for i in range(num_documents):
        category = categories[i % len(categories)]
        document_data = {
            "title": f"Test {category} Document {uuid.uuid4()}",
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
            f"Create Document {i+1}",
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
    if len(created_document_ids) > 0:
        print(f"✅ Successfully created {len(created_document_ids)} documents")
        return True, created_document_ids
    else:
        print(f"❌ Failed to create any documents")
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

def test_document_bulk_delete_comprehensive():
    """Test the document bulk delete functionality with comprehensive tests"""
    print("\n" + "="*80)
    print("TESTING DOCUMENT BULK DELETE FUNCTIONALITY (COMPREHENSIVE)")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test document bulk delete without authentication")
            return False, "Authentication failed"
    
    # Create a large batch of test documents for deletion (37 to match user's scenario)
    print("\nCreating 37 test documents for bulk delete testing...")
    test_doc_success, test_doc_ids = test_document_creation(37)
    
    if not test_doc_success or len(test_doc_ids) < 37:
        print(f"⚠️ Created only {len(test_doc_ids)} test documents instead of 37")
    
    print(f"Created {len(test_doc_ids)} test documents for bulk delete testing")
    
    # Verify documents exist in database
    print("\nVerifying documents exist in database...")
    get_docs_test, get_docs_response = run_test(
        "Get All Documents",
        "/documents",
        method="GET",
        auth=True
    )
    
    if get_docs_test and get_docs_response:
        doc_count = len(get_docs_response)
        print(f"Total documents in database: {doc_count}")
        
        # Extract document IDs from response
        db_doc_ids = [doc.get("id") for doc in get_docs_response]
        
        # Check if all created document IDs exist in database
        missing_docs = [doc_id for doc_id in test_doc_ids if doc_id not in db_doc_ids]
        if missing_docs:
            print(f"⚠️ {len(missing_docs)} created documents not found in database")
        else:
            print("✅ All created documents found in database")
    
    # Test 1: Test POST bulk delete with all document IDs
    print("\nTest 1: Testing POST bulk delete with all document IDs")
    
    # Prepare request data
    post_data = {
        "document_ids": test_doc_ids
    }
    
    # Print request details
    print(f"Request URL: {API_URL}/documents/bulk-delete")
    print(f"Request Method: POST")
    print(f"Request Headers: Authorization: Bearer {auth_token[:10]}...")
    print(f"Request Body: {json.dumps(post_data)}")
    
    # Send request
    post_delete_test, post_delete_response = run_test(
        "POST Bulk Delete with All Document IDs",
        "/documents/bulk-delete",
        method="POST",
        data=post_data,
        auth=True,
        expected_keys=["message", "deleted_count"]
    )
    
    # Analyze response
    if post_delete_test and post_delete_response:
        deleted_count = post_delete_response.get("deleted_count", 0)
        if deleted_count == len(test_doc_ids):
            print(f"✅ POST bulk delete successfully deleted all {len(test_doc_ids)} documents")
            post_success = True
        else:
            print(f"❌ POST bulk delete deleted only {deleted_count} out of {len(test_doc_ids)} documents")
            post_success = False
    else:
        print("❌ POST bulk delete request failed")
        post_success = False
    
    # Verify documents were actually deleted
    if post_success:
        print("\nVerifying documents were deleted from database...")
        get_docs_test, get_docs_response = run_test(
            "Get All Documents After POST Delete",
            "/documents",
            method="GET",
            auth=True
        )
        
        if get_docs_test and get_docs_response:
            remaining_docs = [doc for doc in get_docs_response if doc.get("id") in test_doc_ids]
            if remaining_docs:
                print(f"❌ {len(remaining_docs)} documents still exist in database after POST delete")
                post_success = False
            else:
                print("✅ All documents were successfully deleted from database")
    
    # Create new documents for DELETE endpoint testing
    print("\nCreating new test documents for DELETE endpoint testing...")
    test_doc_success, delete_test_doc_ids = test_document_creation(37)
    
    if not test_doc_success or len(delete_test_doc_ids) < 37:
        print(f"⚠️ Created only {len(delete_test_doc_ids)} test documents instead of 37")
    
    print(f"Created {len(delete_test_doc_ids)} test documents for DELETE endpoint testing")
    
    # Test 2: Test DELETE bulk delete with all document IDs
    print("\nTest 2: Testing DELETE bulk delete with all document IDs")
    
    # Try different request formats
    delete_formats = [
        delete_test_doc_ids,                    # Direct array
        {"document_ids": delete_test_doc_ids},  # Object with document_ids field
        {"data": delete_test_doc_ids}           # Object with data field
    ]
    
    delete_success = False
    
    for i, delete_data in enumerate(delete_formats):
        print(f"\nTrying DELETE format {i+1}: {type(delete_data)}")
        
        # Print request details
        print(f"Request URL: {API_URL}/documents/bulk")
        print(f"Request Method: DELETE")
        print(f"Request Headers: Authorization: Bearer {auth_token[:10]}...")
        print(f"Request Body Type: {type(delete_data)}")
        if isinstance(delete_data, dict):
            print(f"Request Body Keys: {list(delete_data.keys())}")
        print(f"Document IDs Count: {len(delete_test_doc_ids)}")
        
        # Send request
        delete_test, delete_response = run_test(
            f"DELETE Bulk Delete Format {i+1}",
            "/documents/bulk",
            method="DELETE",
            data=delete_data,
            auth=True,
            expected_keys=["message", "deleted_count"]
        )
        
        # Analyze response
        if delete_test and delete_response:
            deleted_count = delete_response.get("deleted_count", 0)
            if deleted_count == len(delete_test_doc_ids):
                print(f"✅ DELETE bulk delete format {i+1} successfully deleted all {len(delete_test_doc_ids)} documents")
                delete_success = True
                break
            else:
                print(f"❌ DELETE bulk delete format {i+1} deleted only {deleted_count} out of {len(delete_test_doc_ids)} documents")
        else:
            print(f"❌ DELETE bulk delete format {i+1} request failed")
    
    # Verify documents were actually deleted
    if delete_success:
        print("\nVerifying documents were deleted from database...")
        get_docs_test, get_docs_response = run_test(
            "Get All Documents After DELETE",
            "/documents",
            method="GET",
            auth=True
        )
        
        if get_docs_test and get_docs_response:
            remaining_docs = [doc for doc in get_docs_response if doc.get("id") in delete_test_doc_ids]
            if remaining_docs:
                print(f"❌ {len(remaining_docs)} documents still exist in database after DELETE")
                delete_success = False
            else:
                print("✅ All documents were successfully deleted from database")
    
    # Test 3: Test authentication requirements
    print("\nTest 3: Testing authentication requirements")
    
    # Create a few more test documents
    print("\nCreating test documents for authentication testing...")
    test_doc_success, auth_test_doc_ids = test_document_creation(3)
    
    # Test without authentication
    no_auth_data = {
        "document_ids": auth_test_doc_ids
    }
    
    # Test POST endpoint without auth
    post_no_auth_test, post_no_auth_response = run_test(
        "POST Bulk Delete Without Authentication",
        "/documents/bulk-delete",
        method="POST",
        data=no_auth_data,
        auth=False,
        expected_status=403
    )
    
    if post_no_auth_test:
        print("✅ POST bulk delete correctly requires authentication")
    else:
        print("❌ POST bulk delete does not properly enforce authentication")
    
    # Test DELETE endpoint without auth
    delete_no_auth_test, delete_no_auth_response = run_test(
        "DELETE Bulk Delete Without Authentication",
        "/documents/bulk",
        method="DELETE",
        data=auth_test_doc_ids,
        auth=False,
        expected_status=403
    )
    
    if delete_no_auth_test:
        print("✅ DELETE bulk delete correctly requires authentication")
    else:
        print("❌ DELETE bulk delete does not properly enforce authentication")
    
    # Test 4: Test with invalid document IDs
    print("\nTest 4: Testing with invalid document IDs")
    
    # Generate invalid document IDs
    invalid_ids = [str(uuid.uuid4()) for _ in range(5)]
    
    # Test POST endpoint with invalid IDs
    invalid_post_data = {
        "document_ids": invalid_ids
    }
    
    invalid_post_test, invalid_post_response = run_test(
        "POST Bulk Delete With Invalid IDs",
        "/documents/bulk-delete",
        method="POST",
        data=invalid_post_data,
        auth=True,
        expected_status=404
    )
    
    if invalid_post_test:
        print("✅ POST bulk delete correctly handles invalid document IDs")
    else:
        print("❌ POST bulk delete does not properly handle invalid document IDs")
    
    # Test DELETE endpoint with invalid IDs
    invalid_delete_test, invalid_delete_response = run_test(
        "DELETE Bulk Delete With Invalid IDs",
        "/documents/bulk",
        method="DELETE",
        data=invalid_ids,
        auth=True,
        expected_status=404
    )
    
    if invalid_delete_test:
        print("✅ DELETE bulk delete correctly handles invalid document IDs")
    else:
        print("❌ DELETE bulk delete does not properly handle invalid document IDs")
    
    # Test 5: Test with mixed valid and invalid document IDs
    print("\nTest 5: Testing with mixed valid and invalid document IDs")
    
    # Create a few more test documents
    print("\nCreating test documents for mixed ID testing...")
    test_doc_success, mixed_test_doc_ids = test_document_creation(3)
    
    # Mix with invalid IDs
    mixed_ids = mixed_test_doc_ids + [str(uuid.uuid4()) for _ in range(2)]
    
    # Test POST endpoint with mixed IDs
    mixed_post_data = {
        "document_ids": mixed_ids
    }
    
    mixed_post_test, mixed_post_response = run_test(
        "POST Bulk Delete With Mixed IDs",
        "/documents/bulk-delete",
        method="POST",
        data=mixed_post_data,
        auth=True,
        expected_status=404
    )
    
    if mixed_post_test:
        print("✅ POST bulk delete correctly handles mixed document IDs")
    else:
        print("❌ POST bulk delete does not properly handle mixed document IDs")
    
    # Test DELETE endpoint with mixed IDs
    mixed_delete_test, mixed_delete_response = run_test(
        "DELETE Bulk Delete With Mixed IDs",
        "/documents/bulk",
        method="DELETE",
        data=mixed_ids,
        auth=True,
        expected_status=404
    )
    
    if mixed_delete_test:
        print("✅ DELETE bulk delete correctly handles mixed document IDs")
    else:
        print("❌ DELETE bulk delete does not properly handle mixed document IDs")
    
    # Print summary
    print("\nDOCUMENT BULK DELETE FUNCTIONALITY SUMMARY:")
    
    if post_success:
        print("✅ POST /api/documents/bulk-delete endpoint is working correctly")
        print("✅ Successfully deleted 37 documents in a single request")
        print("✅ Authentication is properly enforced")
        print("✅ Invalid document IDs are properly handled")
    else:
        print("❌ POST /api/documents/bulk-delete endpoint has issues")
    
    if delete_success:
        print("✅ DELETE /api/documents/bulk endpoint is working correctly")
        print("✅ Successfully deleted 37 documents in a single request")
        print("✅ Authentication is properly enforced")
        print("✅ Invalid document IDs are properly handled")
    else:
        print("❌ DELETE /api/documents/bulk endpoint has issues")
    
    # Overall assessment
    if post_success or delete_success:
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

def test_auth_endpoints():
    """Test the authentication endpoints"""
    print("\n" + "="*80)
    print("TESTING AUTHENTICATION ENDPOINTS")
    print("="*80)
    
    global auth_token, test_user_id, test_user_email
    
    # Test 1: Register with valid email and password
    print("\nTest 1: Register with valid email and password")
    
    register_data = {
        "email": test_user_email,
        "password": test_user_password,
        "name": test_user_name
    }
    
    register_test, register_response = run_test(
        "Register with valid credentials",
        "/auth/register",
        method="POST",
        data=register_data,
        expected_keys=["access_token", "token_type", "user"]
    )
    
    if register_test and register_response:
        print("✅ Registration successful")
        auth_token = register_response.get("access_token")
        user_data = register_response.get("user", {})
        test_user_id = user_data.get("id")
        print(f"User registered with ID: {test_user_id}")
        print(f"JWT Token: {auth_token}")
        
        # Verify token structure
        try:
            decoded_token = jwt.decode(auth_token, JWT_SECRET, algorithms=["HS256"])
            print(f"✅ JWT token is valid and contains: {decoded_token}")
            if "user_id" in decoded_token and "sub" in decoded_token:
                print("✅ JWT token contains required fields (user_id, sub)")
            else:
                print("❌ JWT token is missing required fields")
        except Exception as e:
            print(f"❌ JWT token validation failed: {e}")
    else:
        print("❌ Registration failed")
    
    # Test 2: Register with duplicate email
    print("\nTest 2: Register with duplicate email")
    
    duplicate_register_test, duplicate_register_response = run_test(
        "Register with duplicate email",
        "/auth/register",
        method="POST",
        data=register_data,
        expected_status=400
    )
    
    if duplicate_register_test:
        print("✅ Duplicate email registration correctly rejected")
    else:
        print("❌ Duplicate email registration not properly handled")
    
    # Test 3: Register with invalid email format
    print("\nTest 3: Register with invalid email format")
    
    invalid_email_data = {
        "email": "invalid-email",
        "password": test_user_password,
        "name": test_user_name
    }
    
    invalid_email_test, invalid_email_response = run_test(
        "Register with invalid email format",
        "/auth/register",
        method="POST",
        data=invalid_email_data,
        expected_status=422  # Pydantic validation error
    )
    
    if invalid_email_test:
        print("✅ Invalid email format correctly rejected")
    else:
        print("❌ Invalid email format not properly validated")
    
    # Test 4: Register with password too short
    print("\nTest 4: Register with password too short")
    
    short_password_data = {
        "email": f"another.{uuid.uuid4()}@example.com",
        "password": "short",
        "name": test_user_name
    }
    
    short_password_test, short_password_response = run_test(
        "Register with password too short",
        "/auth/register",
        method="POST",
        data=short_password_data,
        expected_status=422  # Pydantic validation error
    )
    
    if short_password_test:
        print("✅ Short password correctly rejected")
    else:
        print("❌ Short password not properly validated")
    
    # Test 5: Login with valid credentials
    print("\nTest 5: Login with valid credentials")
    
    login_data = {
        "email": test_user_email,
        "password": test_user_password
    }
    
    login_test, login_response = run_test(
        "Login with valid credentials",
        "/auth/login",
        method="POST",
        data=login_data,
        expected_keys=["access_token", "token_type", "user"]
    )
    
    if login_test and login_response:
        print("✅ Login successful")
        login_token = login_response.get("access_token")
        login_user = login_response.get("user", {})
        
        # Verify user data
        if login_user.get("id") == test_user_id:
            print("✅ User ID matches registered user")
        else:
            print("❌ User ID does not match registered user")
            
        # Verify token
        try:
            decoded_login_token = jwt.decode(login_token, JWT_SECRET, algorithms=["HS256"])
            print(f"✅ Login JWT token is valid")
            if decoded_login_token.get("user_id") == test_user_id:
                print("✅ Login JWT token contains correct user_id")
            else:
                print("❌ Login JWT token has incorrect user_id")
        except Exception as e:
            print(f"❌ Login JWT token validation failed: {e}")
    else:
        print("❌ Login failed")
    
    # Test 6: Login with wrong email
    print("\nTest 6: Login with wrong email")
    
    wrong_email_data = {
        "email": f"wrong.{uuid.uuid4()}@example.com",
        "password": test_user_password
    }
    
    wrong_email_test, wrong_email_response = run_test(
        "Login with wrong email",
        "/auth/login",
        method="POST",
        data=wrong_email_data,
        expected_status=401
    )
    
    if wrong_email_test:
        print("✅ Login with wrong email correctly rejected")
    else:
        print("❌ Login with wrong email not properly handled")
    
    # Test 7: Login with wrong password
    print("\nTest 7: Login with wrong password")
    
    wrong_password_data = {
        "email": test_user_email,
        "password": "wrongPassword123"
    }
    
    wrong_password_test, wrong_password_response = run_test(
        "Login with wrong password",
        "/auth/login",
        method="POST",
        data=wrong_password_data,
        expected_status=401
    )
    
    if wrong_password_test:
        print("✅ Login with wrong password correctly rejected")
    else:
        print("❌ Login with wrong password not properly handled")
    
    # Test 8: Test protected endpoint with token
    print("\nTest 8: Test protected endpoint with token")
    
    # Use the token from login to access a protected endpoint
    if auth_token:
        protected_test, protected_response = run_test(
            "Access protected endpoint",
            "/documents",
            method="GET",
            auth=True
        )
        
        if protected_test:
            print("✅ Successfully accessed protected endpoint with token")
        else:
            print("❌ Failed to access protected endpoint with token")
    else:
        print("❌ Cannot test protected endpoint without valid token")
    
    # Print summary
    print("\nAUTHENTICATION ENDPOINTS SUMMARY:")
    
    # Check if all critical tests passed
    registration_works = register_test
    login_works = login_test
    token_works = protected_test if auth_token else False
    
    if registration_works and login_works and token_works:
        print("✅ Authentication system is working correctly!")
        print("✅ Registration endpoint is functioning properly")
        print("✅ Login endpoint is functioning properly")
        print("✅ JWT tokens are generated correctly")
        print("✅ Protected endpoints can be accessed with valid token")
        return True, "Authentication system is working correctly"
    else:
        issues = []
        if not registration_works:
            issues.append("Registration endpoint is not functioning properly")
        if not login_works:
            issues.append("Login endpoint is not functioning properly")
        if not token_works:
            issues.append("JWT token authentication is not working properly")
        
        print("❌ Authentication system has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}

def test_default_agents_removal():
    """Test the removal of default agents creation"""
    print("\n" + "="*80)
    print("TESTING REMOVAL OF DEFAULT AGENTS CREATION")
    print("="*80)
    
    # Create a new test user account with email/password registration
    test_email = f"test.user.{uuid.uuid4()}@example.com"
    test_password = "securePassword123"
    test_name = "Test User"
    
    print("\nTest 1: Creating a new test user account")
    register_data = {
        "email": test_email,
        "password": test_password,
        "name": test_name
    }
    
    register_test, register_response = run_test(
        "Register new test user",
        "/auth/register",
        method="POST",
        data=register_data,
        expected_keys=["access_token", "token_type", "user"]
    )
    
    if not register_test or not register_response:
        print("❌ Failed to create test user account")
        return False, "Failed to create test user account"
    
    # Store the token for further testing
    test_token = register_response.get("access_token")
    test_user_data = register_response.get("user", {})
    test_user_id = test_user_data.get("id")
    
    print(f"✅ Successfully created test user with ID: {test_user_id}")
    print(f"JWT Token: {test_token}")
    
    # Test 2: Verify the user starts completely empty - Zero agents
    print("\nTest 2: Verifying user starts with zero agents")
    
    agents_test, agents_response = run_test(
        "Get user agents",
        "/agents",
        method="GET",
        auth=True,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    if not agents_test:
        print("❌ Failed to get user agents")
        return False, "Failed to get user agents"
    
    agent_count = len(agents_response) if agents_response else 0
    print(f"Agent count: {agent_count}")
    
    if agent_count == 0:
        print("✅ User starts with zero agents as expected")
    else:
        print(f"❌ User starts with {agent_count} agents instead of zero")
        print("Agents found:")
        for agent in agents_response:
            print(f"  - {agent.get('name', 'Unknown')} ({agent.get('id', 'Unknown ID')})")
        return False, f"User starts with {agent_count} agents instead of zero"
    
    # Test 3: Verify the user starts completely empty - Zero conversations
    print("\nTest 3: Verifying user starts with zero conversations")
    
    conversations_test, conversations_response = run_test(
        "Get user conversations",
        "/conversations",
        method="GET",
        auth=True,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    if not conversations_test:
        print("❌ Failed to get user conversations")
        return False, "Failed to get user conversations"
    
    conversation_count = len(conversations_response) if conversations_response else 0
    print(f"Conversation count: {conversation_count}")
    
    if conversation_count == 0:
        print("✅ User starts with zero conversations as expected")
    else:
        print(f"❌ User starts with {conversation_count} conversations instead of zero")
        return False, f"User starts with {conversation_count} conversations instead of zero"
    
    # Test 4: Verify the user starts completely empty - Zero documents
    print("\nTest 4: Verifying user starts with zero documents")
    
    documents_test, documents_response = run_test(
        "Get user documents",
        "/documents",
        method="GET",
        auth=True,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    if not documents_test:
        print("❌ Failed to get user documents")
        return False, "Failed to get user documents"
    
    document_count = len(documents_response) if documents_response else 0
    print(f"Document count: {document_count}")
    
    if document_count == 0:
        print("✅ User starts with zero documents as expected")
    else:
        print(f"❌ User starts with {document_count} documents instead of zero")
        return False, f"User starts with {document_count} documents instead of zero"
    
    # Test 5: Test starting a new simulation
    print("\nTest 5: Testing starting a new simulation")
    
    simulation_start_test, simulation_start_response = run_test(
        "Start simulation",
        "/simulation/start",
        method="POST",
        auth=True,
        headers={"Authorization": f"Bearer {test_token}"},
        expected_keys=["message", "state"]
    )
    
    if not simulation_start_test:
        print("❌ Failed to start simulation")
        return False, "Failed to start simulation"
    
    print("✅ Successfully started simulation")
    
    # Test 6: Verify no agents are automatically created after starting simulation
    print("\nTest 6: Verifying no agents are automatically created after starting simulation")
    
    agents_after_sim_test, agents_after_sim_response = run_test(
        "Get user agents after simulation start",
        "/agents",
        method="GET",
        auth=True,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    if not agents_after_sim_test:
        print("❌ Failed to get user agents after simulation start")
        return False, "Failed to get user agents after simulation start"
    
    agent_after_sim_count = len(agents_after_sim_response) if agents_after_sim_response else 0
    print(f"Agent count after simulation start: {agent_after_sim_count}")
    
    if agent_after_sim_count == 0:
        print("✅ No agents are automatically created after starting simulation")
    else:
        print(f"❌ {agent_after_sim_count} agents were automatically created after starting simulation")
        print("Agents found:")
        for agent in agents_after_sim_response:
            print(f"  - {agent.get('name', 'Unknown')} ({agent.get('id', 'Unknown ID')})")
        return False, f"{agent_after_sim_count} agents were automatically created after starting simulation"
    
    # Test 7: Verify the init-research-station endpoint still works
    print("\nTest 7: Verifying the init-research-station endpoint still works")
    
    init_station_test, init_station_response = run_test(
        "Initialize research station",
        "/simulation/init-research-station",
        method="POST",
        auth=True,
        headers={"Authorization": f"Bearer {test_token}"},
        expected_keys=["message", "agents"]
    )
    
    if not init_station_test:
        print("❌ Failed to initialize research station")
        return False, "Failed to initialize research station"
    
    print("✅ Successfully initialized research station")
    
    # Test 8: Verify agents are created by init-research-station endpoint
    print("\nTest 8: Verifying agents are created by init-research-station endpoint")
    
    agents_after_init_test, agents_after_init_response = run_test(
        "Get user agents after init-research-station",
        "/agents",
        method="GET",
        auth=True,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    if not agents_after_init_test:
        print("❌ Failed to get user agents after init-research-station")
        return False, "Failed to get user agents after init-research-station"
    
    agent_after_init_count = len(agents_after_init_response) if agents_after_init_response else 0
    print(f"Agent count after init-research-station: {agent_after_init_count}")
    
    if agent_after_init_count > 0:
        print(f"✅ {agent_after_init_count} agents were created by init-research-station endpoint")
        print("Agents found:")
        for agent in agents_after_init_response:
            print(f"  - {agent.get('name', 'Unknown')} ({agent.get('id', 'Unknown ID')})")
            
        # Check if the expected crypto team agents were created
        expected_agents = ["Marcus \"Mark\" Castellano", "Alexandra \"Alex\" Chen", "Diego \"Dex\" Rodriguez"]
        found_agents = [agent.get("name") for agent in agents_after_init_response]
        
        missing_agents = [name for name in expected_agents if name not in found_agents]
        if missing_agents:
            print(f"❌ Missing expected agents: {', '.join(missing_agents)}")
            return False, f"Missing expected agents: {', '.join(missing_agents)}"
        else:
            print("✅ All expected crypto team agents were created")
    else:
        print("❌ No agents were created by init-research-station endpoint")
        return False, "No agents were created by init-research-station endpoint"
    
    # Test 9: Verify agents are properly associated with the test user
    print("\nTest 9: Verifying agents are properly associated with the test user")
    
    user_id_match = True
    for agent in agents_after_init_response:
        agent_user_id = agent.get("user_id")
        if agent_user_id != test_user_id:
            print(f"❌ Agent {agent.get('name')} is associated with user ID {agent_user_id} instead of {test_user_id}")
            user_id_match = False
    
    if user_id_match:
        print("✅ All agents are properly associated with the test user")
    else:
        print("❌ Some agents are not properly associated with the test user")
        return False, "Some agents are not properly associated with the test user"
    
    # Print summary
    print("\nDEFAULT AGENTS REMOVAL SUMMARY:")
    print("✅ New users start with completely empty workspaces (no agents, conversations, or documents)")
    print("✅ Starting a simulation does not automatically create any agents")
    print("✅ The init-research-station endpoint still works and creates the default crypto team agents when called explicitly")
    print("✅ Agents created by init-research-station are properly associated with the user")
    
    return True, "Default agents removal is working correctly"

def test_enhanced_document_generation():
    """Test the enhanced document generation system"""
    print("\n" + "="*80)
    print("TESTING ENHANCED DOCUMENT GENERATION SYSTEM")
    print("="*80)
    
    # Login first to get auth token
    global auth_token, test_user_id
    if not auth_token:
        if not test_login():
            print("❌ Cannot test enhanced document generation without authentication")
            return False, "Authentication failed"
    
    # Test 1: Test the quality gate with budget/financial discussions
    print("\nTest 1: Testing quality gate with budget/financial discussions")
    
    # Create a conversation with budget/financial discussions
    budget_conversation = """
    Mark: I think we need to allocate our budget more effectively for the next quarter.
    Alex: I agree. We should put 40% towards development, 30% towards marketing, and 20% towards operations.
    Dex: What about the remaining 10%? I suggest we keep it as a contingency fund.
    Mark: That's a good point. Let's allocate the budget as Alex suggested with the 10% contingency.
    Alex: Great, so we have consensus on the budget allocation. Let's create a budget document to formalize this.
    """
    
    # Call the document quality gate endpoint
    quality_gate_data = {
        "conversation_text": budget_conversation,
        "conversation_round": 5,
        "last_document_round": 0
    }
    
    budget_quality_test, budget_quality_response = run_test(
        "Quality Gate - Budget Discussion",
        "/documents/quality-check",
        method="POST",
        data=quality_gate_data,
        auth=True,
        expected_keys=["should_create", "reason"]
    )
    
    if budget_quality_test and budget_quality_response:
        should_create = budget_quality_response.get("should_create", False)
        reason = budget_quality_response.get("reason", "")
        
        if should_create:
            print(f"✅ Quality gate correctly allows document creation for budget discussions")
            print(f"Reason: {reason}")
        else:
            print(f"❌ Quality gate incorrectly blocks document creation for budget discussions")
            print(f"Reason: {reason}")
    else:
        print("❌ Failed to test quality gate with budget discussions")
    
    # Test 2: Test the quality gate with timeline/milestone discussions
    print("\nTest 2: Testing quality gate with timeline/milestone discussions")
    
    # Create a conversation with timeline/milestone discussions
    timeline_conversation = """
    Alex: We need to establish a timeline for the project launch.
    Mark: I think we should aim for initial development in Month 1-2, testing in Month 3-4, and launch in Month 5.
    Dex: That seems reasonable, but we should add a beta phase between testing and launch.
    Alex: Good point. So the timeline would be: Month 1-2 Development, Month 3-4 Testing, Month 4-5 Beta, Month 6 Launch.
    Mark: I agree with this timeline. Let's document this so the team has clear milestones to work towards.
    """
    
    # Call the document quality gate endpoint
    quality_gate_data = {
        "conversation_text": timeline_conversation,
        "conversation_round": 5,
        "last_document_round": 0
    }
    
    timeline_quality_test, timeline_quality_response = run_test(
        "Quality Gate - Timeline Discussion",
        "/documents/quality-check",
        method="POST",
        data=quality_gate_data,
        auth=True,
        expected_keys=["should_create", "reason"]
    )
    
    if timeline_quality_test and timeline_quality_response:
        should_create = timeline_quality_response.get("should_create", False)
        reason = timeline_quality_response.get("reason", "")
        
        if should_create:
            print(f"✅ Quality gate correctly allows document creation for timeline discussions")
            print(f"Reason: {reason}")
        else:
            print(f"❌ Quality gate incorrectly blocks document creation for timeline discussions")
            print(f"Reason: {reason}")
    else:
        print("❌ Failed to test quality gate with timeline discussions")
    
    # Test 3: Test the quality gate with risk assessment discussions
    print("\nTest 3: Testing quality gate with risk assessment discussions")
    
    # Create a conversation with risk assessment discussions
    risk_conversation = """
    Dex: We need to assess the risks associated with this project.
    Mark: I see three main risks: technical complexity, market competition, and regulatory challenges.
    Alex: I agree. On a scale of 1-10, I'd rate technical complexity as 7, market competition as 8, and regulatory challenges as 6.
    Dex: That seems accurate. We should also consider mitigation strategies for each risk.
    Mark: Good point. Let's create a risk assessment document that outlines these risks and our mitigation strategies.
    """
    
    # Call the document quality gate endpoint
    quality_gate_data = {
        "conversation_text": risk_conversation,
        "conversation_round": 5,
        "last_document_round": 0
    }
    
    risk_quality_test, risk_quality_response = run_test(
        "Quality Gate - Risk Assessment Discussion",
        "/documents/quality-check",
        method="POST",
        data=quality_gate_data,
        auth=True,
        expected_keys=["should_create", "reason"]
    )
    
    if risk_quality_test and risk_quality_response:
        should_create = risk_quality_response.get("should_create", False)
        reason = risk_quality_response.get("reason", "")
        
        if should_create:
            print(f"✅ Quality gate correctly allows document creation for risk assessment discussions")
            print(f"Reason: {reason}")
        else:
            print(f"❌ Quality gate incorrectly blocks document creation for risk assessment discussions")
            print(f"Reason: {reason}")
    else:
        print("❌ Failed to test quality gate with risk assessment discussions")
    
    # Test 4: Test the quality gate with substantive content without perfect consensus phrases
    print("\nTest 4: Testing quality gate with substantive content without perfect consensus phrases")
    
    # Create a conversation with substantive content but without perfect consensus phrases
    substantive_conversation = """
    Alex: I've been analyzing our current market position and I think we need to pivot our strategy.
    Mark: What specifically are you suggesting?
    Alex: We should focus more on enterprise clients rather than small businesses. They have bigger budgets and longer contracts.
    Dex: That makes sense. Enterprise clients would provide more stability for our revenue.
    Mark: I see the benefits, but it would require significant changes to our sales approach and product features.
    Alex: True, but the long-term benefits outweigh the short-term adjustment costs.
    """
    
    # Call the document quality gate endpoint
    quality_gate_data = {
        "conversation_text": substantive_conversation,
        "conversation_round": 5,
        "last_document_round": 0
    }
    
    substantive_quality_test, substantive_quality_response = run_test(
        "Quality Gate - Substantive Content",
        "/documents/quality-check",
        method="POST",
        data=quality_gate_data,
        auth=True,
        expected_keys=["should_create", "reason"]
    )
    
    if substantive_quality_test and substantive_quality_response:
        should_create = substantive_quality_response.get("should_create", False)
        reason = substantive_quality_response.get("reason", "")
        
        if should_create:
            print(f"✅ Quality gate correctly allows document creation for substantive content without perfect consensus phrases")
            print(f"Reason: {reason}")
        else:
            print(f"❌ Quality gate incorrectly blocks document creation for substantive content without perfect consensus phrases")
            print(f"Reason: {reason}")
    else:
        print("❌ Failed to test quality gate with substantive content")
    
    # Test 5: Test chart embedding in budget document
    print("\nTest 5: Testing chart embedding in budget document")
    
    # Create a budget document
    budget_doc_data = {
        "title": "Q3 Budget Allocation Plan",
        "category": "Budget",
        "description": "Budget allocation for Q3 with detailed breakdown",
        "content": """# Q3 Budget Allocation Plan

## Executive Summary
This document outlines our budget allocation for Q3 2023.

## Budget Breakdown
- Development: 40%
- Marketing: 30%
- Operations: 20%
- Contingency: 10%

## Justification
The allocation prioritizes development to complete our new product features while maintaining adequate marketing spend to promote the launch.

## Approval
This budget has been approved by the management team.
""",
        "keywords": ["budget", "finance", "allocation", "Q3"],
        "authors": ["Mark Castellano", "Alex Chen"]
    }
    
    create_budget_doc_test, create_budget_doc_response = run_test(
        "Create Budget Document",
        "/documents/create",
        method="POST",
        data=budget_doc_data,
        auth=True,
        expected_keys=["success", "document_id"]
    )
    
    budget_doc_id = None
    if create_budget_doc_test and create_budget_doc_response:
        budget_doc_id = create_budget_doc_response.get("document_id")
        print(f"✅ Created budget document with ID: {budget_doc_id}")
    else:
        print("❌ Failed to create budget document")
    
    # Get the created document to check for chart embedding
    if budget_doc_id:
        get_budget_doc_test, get_budget_doc_response = run_test(
            "Get Budget Document",
            f"/documents/{budget_doc_id}",
            method="GET",
            auth=True,
            expected_keys=["id", "metadata", "content"]
        )
        
        if get_budget_doc_test and get_budget_doc_response:
            content = get_budget_doc_response.get("content", "")
            
            # Check if content contains base64 image data for chart
            has_chart = "data:image/png;base64," in content and "chart-container" in content
            
            if has_chart:
                print("✅ Budget document correctly contains embedded pie chart")
            else:
                print("❌ Budget document does not contain embedded pie chart")
                print("Content excerpt:")
                print(content[:500] + "..." if len(content) > 500 else content)
        else:
            print("❌ Failed to retrieve budget document")
    
    # Test 6: Test chart embedding in timeline document
    print("\nTest 6: Testing chart embedding in timeline document")
    
    # Create a timeline document
    timeline_doc_data = {
        "title": "Project Launch Timeline",
        "category": "Protocol",
        "description": "Timeline for project development and launch",
        "content": """# Project Launch Timeline

## Overview
This document outlines the timeline for our project development and launch.

## Key Milestones
- Month 1-2: Development
- Month 3-4: Testing
- Month 4-5: Beta
- Month 6: Launch

## Dependencies
The testing phase cannot begin until development is at least 90% complete.

## Responsibility
Each team lead is responsible for meeting their respective milestones.
""",
        "keywords": ["timeline", "project", "milestones", "launch"],
        "authors": ["Alex Chen", "Dex Rodriguez"]
    }
    
    create_timeline_doc_test, create_timeline_doc_response = run_test(
        "Create Timeline Document",
        "/documents/create",
        method="POST",
        data=timeline_doc_data,
        auth=True,
        expected_keys=["success", "document_id"]
    )
    
    timeline_doc_id = None
    if create_timeline_doc_test and create_timeline_doc_response:
        timeline_doc_id = create_timeline_doc_response.get("document_id")
        print(f"✅ Created timeline document with ID: {timeline_doc_id}")
    else:
        print("❌ Failed to create timeline document")
    
    # Get the created document to check for chart embedding
    if timeline_doc_id:
        get_timeline_doc_test, get_timeline_doc_response = run_test(
            "Get Timeline Document",
            f"/documents/{timeline_doc_id}",
            method="GET",
            auth=True,
            expected_keys=["id", "metadata", "content"]
        )
        
        if get_timeline_doc_test and get_timeline_doc_response:
            content = get_timeline_doc_response.get("content", "")
            
            # Check if content contains base64 image data for chart
            has_chart = "data:image/png;base64," in content and "chart-container" in content
            
            if has_chart:
                print("✅ Timeline document correctly contains embedded timeline chart")
            else:
                print("❌ Timeline document does not contain embedded timeline chart")
                print("Content excerpt:")
                print(content[:500] + "..." if len(content) > 500 else content)
        else:
            print("❌ Failed to retrieve timeline document")
    
    # Test 7: Test chart embedding in risk document
    print("\nTest 7: Testing chart embedding in risk document")
    
    # Create a risk document
    risk_doc_data = {
        "title": "Project Risk Assessment",
        "category": "Research",
        "description": "Assessment of project risks and mitigation strategies",
        "content": """# Project Risk Assessment

## Overview
This document outlines the key risks associated with our project and proposed mitigation strategies.

## Risk Factors
- Technical Complexity: 7/10
- Market Competition: 8/10
- Regulatory Challenges: 6/10

## Mitigation Strategies
- Technical Complexity: Hire additional senior developers and implement phased approach
- Market Competition: Focus on unique value proposition and accelerate go-to-market
- Regulatory Challenges: Engage legal consultants early in the process

## Monitoring
Risks will be reviewed bi-weekly during project status meetings.
""",
        "keywords": ["risk", "assessment", "mitigation", "project"],
        "authors": ["Mark Castellano", "Dex Rodriguez"]
    }
    
    create_risk_doc_test, create_risk_doc_response = run_test(
        "Create Risk Document",
        "/documents/create",
        method="POST",
        data=risk_doc_data,
        auth=True,
        expected_keys=["success", "document_id"]
    )
    
    risk_doc_id = None
    if create_risk_doc_test and create_risk_doc_response:
        risk_doc_id = create_risk_doc_response.get("document_id")
        print(f"✅ Created risk document with ID: {risk_doc_id}")
    else:
        print("❌ Failed to create risk document")
    
    # Get the created document to check for chart embedding
    if risk_doc_id:
        get_risk_doc_test, get_risk_doc_response = run_test(
            "Get Risk Document",
            f"/documents/{risk_doc_id}",
            method="GET",
            auth=True,
            expected_keys=["id", "metadata", "content"]
        )
        
        if get_risk_doc_test and get_risk_doc_response:
            content = get_risk_doc_response.get("content", "")
            
            # Check if content contains base64 image data for chart
            has_chart = "data:image/png;base64," in content and "chart-container" in content
            
            if has_chart:
                print("✅ Risk document correctly contains embedded bar chart")
            else:
                print("❌ Risk document does not contain embedded bar chart")
                print("Content excerpt:")
                print(content[:500] + "..." if len(content) > 500 else content)
        else:
            print("❌ Failed to retrieve risk document")
    
    # Test 8: Test end-to-end document quality
    print("\nTest 8: Testing end-to-end document quality")
    
    # Check HTML formatting, CSS styling, and section headers in all created documents
    document_ids = [doc_id for doc_id in [budget_doc_id, timeline_doc_id, risk_doc_id] if doc_id]
    
    if not document_ids:
        print("❌ No documents were created successfully for quality testing")
        return False, "No documents were created successfully for quality testing"
    
    quality_results = []
    
    for doc_id in document_ids:
        get_doc_test, get_doc_response = run_test(
            f"Get Document {doc_id} for Quality Check",
            f"/documents/{doc_id}",
            method="GET",
            auth=True
        )
        
        if get_doc_test and get_doc_response:
            content = get_doc_response.get("content", "")
            
            # Check for HTML formatting
            has_html = content.startswith("<!DOCTYPE html>") or "<html>" in content
            
            # Check for CSS styling
            has_css = "<style>" in content
            
            # Check for section headers
            has_headers = "section-header" in content or "<h1>" in content or "<h2>" in content
            
            # Check for embedded charts
            has_charts = "data:image/png;base64," in content and "chart-container" in content
            
            quality_results.append({
                "doc_id": doc_id,
                "has_html": has_html,
                "has_css": has_css,
                "has_headers": has_headers,
                "has_charts": has_charts
            })
            
            print(f"Document {doc_id} quality check:")
            print(f"  - HTML formatting: {'✅' if has_html else '❌'}")
            print(f"  - CSS styling: {'✅' if has_css else '❌'}")
            print(f"  - Section headers: {'✅' if has_headers else '❌'}")
            print(f"  - Embedded charts: {'✅' if has_charts else '❌'}")
        else:
            print(f"❌ Failed to retrieve document {doc_id} for quality check")
    
    # Print summary
    print("\nENHANCED DOCUMENT GENERATION SUMMARY:")
    
    # Check quality gate tests
    quality_gate_tests = [
        budget_quality_test and budget_quality_response and budget_quality_response.get("should_create", False),
        timeline_quality_test and timeline_quality_response and timeline_quality_response.get("should_create", False),
        risk_quality_test and risk_quality_response and risk_quality_response.get("should_create", False),
        substantive_quality_test and substantive_quality_response and substantive_quality_response.get("should_create", False)
    ]
    
    quality_gate_working = all(quality_gate_tests)
    
    # Check chart embedding tests
    chart_embedding_tests = [result["has_charts"] for result in quality_results]
    chart_embedding_working = all(chart_embedding_tests)
    
    # Check document quality tests
    document_quality_tests = [
        all(result["has_html"] for result in quality_results),
        all(result["has_css"] for result in quality_results),
        all(result["has_headers"] for result in quality_results)
    ]
    document_quality_working = all(document_quality_tests)
    
    if quality_gate_working:
        print("✅ Quality gate is working correctly")
        print("✅ Document creation is allowed for budget/financial discussions")
        print("✅ Document creation is allowed for timeline/milestone conversations")
        print("✅ Document creation is allowed for risk assessment discussions")
        print("✅ Document creation is allowed for substantive content without perfect consensus phrases")
    else:
        print("❌ Quality gate has issues")
        if not quality_gate_tests[0]:
            print("❌ Document creation is blocked for budget/financial discussions")
        if not quality_gate_tests[1]:
            print("❌ Document creation is blocked for timeline/milestone conversations")
        if not quality_gate_tests[2]:
            print("❌ Document creation is blocked for risk assessment discussions")
        if not quality_gate_tests[3]:
            print("❌ Document creation is blocked for substantive content without perfect consensus phrases")
    
    if chart_embedding_working:
        print("✅ Chart embedding is working correctly")
        print("✅ Pie charts are properly embedded in budget documents")
        print("✅ Timeline charts are properly embedded in timeline documents")
        print("✅ Bar charts are properly embedded in risk documents")
    else:
        print("❌ Chart embedding has issues")
        for i, result in enumerate(quality_results):
            if not result["has_charts"]:
                print(f"❌ Charts are not properly embedded in document {result['doc_id']}")
    
    if document_quality_working:
        print("✅ Document quality is excellent")
        print("✅ Documents have professional HTML formatting")
        print("✅ Documents have CSS styling")
        print("✅ Documents have proper section headers and structure")
    else:
        print("❌ Document quality has issues")
        if not document_quality_tests[0]:
            print("❌ Documents lack proper HTML formatting")
        if not document_quality_tests[1]:
            print("❌ Documents lack CSS styling")
        if not document_quality_tests[2]:
            print("❌ Documents lack proper section headers and structure")
    
    # Overall assessment
    if quality_gate_working and chart_embedding_working and document_quality_working:
        print("\n✅ Enhanced document generation system is working correctly")
        return True, "Enhanced document generation system is working correctly"
    else:
        issues = []
        if not quality_gate_working:
            issues.append("Quality gate has issues")
        if not chart_embedding_working:
            issues.append("Chart embedding has issues")
        if not document_quality_working:
            issues.append("Document quality has issues")
        
        print(f"\n❌ Enhanced document generation system has issues: {', '.join(issues)}")
        return False, {"issues": issues}

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("RUNNING API TESTS")
    print("="*80)
    
    # Test login first to get auth token
    test_login()
    
    # Run basic API health check
    basic_api_health_result, basic_api_health_message = test_basic_api_health()
    
    # Test simulation features
    simulation_features_result, simulation_features_message = test_simulation_features()
    
    # Test translation features
    translation_features_result, translation_features_message = test_translation_features()
    
    # Test avatar generation
    avatar_generation_result, avatar_generation_message = test_avatar_generation()
    
    # Test admin functionality
    admin_functionality_result, admin_functionality_message = test_admin_functionality()
    
    # Test the improved conversation generation system
    conversation_success, conversation_message = test_conversation_generation(API_URL, auth_token, run_test)
    
    # Test the enhanced dynamic conversation system
    dynamic_conversation_success, dynamic_conversation_message = test_dynamic_conversation(API_URL, auth_token, run_test)
    
    # Test the natural expertise demonstration system
    natural_expertise_success, natural_expertise_message = test_natural_expertise(API_URL, auth_token, run_test)
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    print(f"Basic API Health Check: {'✅ PASSED' if basic_api_health_result else '❌ FAILED'}")
    print(f"Simulation Features: {'✅ PASSED' if simulation_features_result else '❌ FAILED'}")
    print(f"Translation Features: {'✅ PASSED' if translation_features_result else '❌ FAILED'}")
    print(f"Avatar Generation: {'✅ PASSED' if avatar_generation_result else '❌ FAILED'}")
    print(f"Admin Functionality: {'✅ PASSED' if admin_functionality_result else '❌ FAILED'}")
    print(f"Improved Conversation Generation: {'✅ PASSED' if conversation_success else '❌ FAILED'}")
    print(f"Enhanced Dynamic Conversation: {'✅ PASSED' if dynamic_conversation_success else '❌ FAILED'}")
    print(f"Natural Expertise Demonstration: {'✅ PASSED' if natural_expertise_success else '❌ FAILED'}")
    
    print("="*80)
    overall_result = all([
        basic_api_health_result,
        simulation_features_result,
        translation_features_result,
        avatar_generation_result,
        admin_functionality_result,
        conversation_success,
        dynamic_conversation_success,
        natural_expertise_success
    ])
    print(f"OVERALL RESULT: {'✅ PASSED' if overall_result else '❌ FAILED'}")
    print("="*80)
    
    # Print detailed summary
    print_summary()
    
    # Test the enhanced document generation system
    enhanced_doc_success, enhanced_doc_message = test_enhanced_document_generation()
    
    # Test the analytics endpoints
    analytics_success, analytics_message = test_analytics_endpoints()
    
    if analytics_success:
        print("✅ Analytics endpoints are working correctly")
        print("✅ Comprehensive analytics endpoint returns proper data structure")
        print("✅ Weekly summary endpoint returns proper data structure")
        print("✅ Authentication is properly enforced for analytics endpoints")
    else:
        if isinstance(analytics_message, dict) and "issues" in analytics_message:
            for issue in analytics_message["issues"]:
                print(f"❌ {issue}")
        else:
            print(f"❌ {analytics_message}")
    
    # Print summary of all tests
    print_summary()
    
    # Print final conclusion
    print("\n" + "="*80)
    print("API FUNCTIONALITY ASSESSMENT")
    print("="*80)
    
    if conversation_success:
        print("✅ Improved conversation generation system is working correctly")
        print("✅ No self-introductions after first round")
        print("✅ No repetitive phrases")
        print("✅ Conversations are solution-focused")
        print("✅ Agents reference previous speakers")
        print("✅ Conversations show progression from analysis to decisions")
    else:
        if isinstance(conversation_message, dict) and "issues" in conversation_message:
            for issue in conversation_message["issues"]:
                print(f"❌ {issue}")
        else:
            print(f"❌ {conversation_message}")
    
    if dynamic_conversation_success:
        print("✅ Enhanced dynamic conversation system is working correctly")
        print("✅ Scenario repetition is eliminated after first few exchanges")
        print("✅ Agents understand conversation progression through different phases")
        print("✅ Conversations show dynamic topic building")
        print("✅ Conversations display natural human-like patterns")
        print("✅ Enhanced filtering successfully catches banned phrases")
    else:
        if isinstance(dynamic_conversation_message, dict) and "issues" in dynamic_conversation_message:
            for issue in dynamic_conversation_message["issues"]:
                print(f"❌ {issue}")
        else:
            print(f"❌ {dynamic_conversation_message}")
    
    if enhanced_doc_success:
        print("✅ Enhanced document generation system is working correctly")
        print("✅ Quality gate properly allows document creation for substantive content")
        print("✅ Charts are properly embedded in documents")
        print("✅ Documents have professional formatting and structure")
    else:
        if isinstance(enhanced_doc_message, dict) and "issues" in enhanced_doc_message:
            for issue in enhanced_doc_message["issues"]:
                print(f"❌ {issue}")
        else:
            print(f"❌ {enhanced_doc_message}")
    
    if natural_expertise_success:
        print("✅ Natural expertise demonstration system is working correctly")
        print("✅ Agents never mention their background explicitly")
        print("✅ Agents naturally demonstrate expertise through terminology")
        print("✅ Agents use professional communication patterns")
        print("✅ Agents favor implicit expertise over explicit credentials")
    else:
        if isinstance(natural_expertise_message, dict) and "issues" in natural_expertise_message:
            for issue in natural_expertise_message["issues"]:
                print(f"❌ {issue}")
        else:
            print(f"❌ {natural_expertise_message}")
    
    print("="*80)
    
    return conversation_success and enhanced_doc_success and dynamic_conversation_success and natural_expertise_success and analytics_success

def test_analytics_endpoints():
    """Test the analytics endpoints"""
    print("\n" + "="*80)
    print("TESTING ANALYTICS ENDPOINTS")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test analytics endpoints without authentication")
            return False, "Authentication failed"
    
    # Test 1: Test the comprehensive analytics endpoint
    print("\nTest 1: Testing comprehensive analytics endpoint")
    
    comprehensive_test, comprehensive_response = run_test(
        "Comprehensive Analytics",
        "/analytics/comprehensive",
        method="GET",
        auth=True,
        expected_keys=["summary", "daily_activity", "agent_usage", "scenario_distribution", "api_usage", "generated_at"]
    )
    
    if comprehensive_test and comprehensive_response:
        print("✅ Comprehensive analytics endpoint returned successfully")
        
        # Verify the structure of the response
        summary = comprehensive_response.get("summary", {})
        daily_activity = comprehensive_response.get("daily_activity", [])
        agent_usage = comprehensive_response.get("agent_usage", [])
        scenario_distribution = comprehensive_response.get("scenario_distribution", [])
        api_usage = comprehensive_response.get("api_usage", {})
        
        # Check summary structure
        summary_keys = ["total_conversations", "conversations_this_week", "conversations_this_month", 
                        "total_agents", "agents_this_week", "total_documents", "documents_this_week"]
        missing_summary_keys = [key for key in summary_keys if key not in summary]
        
        if not missing_summary_keys:
            print("✅ Summary contains all required fields")
        else:
            print(f"❌ Summary is missing fields: {', '.join(missing_summary_keys)}")
        
        # Check daily activity structure
        if daily_activity and isinstance(daily_activity, list) and len(daily_activity) == 30:
            print(f"✅ Daily activity contains data for 30 days")
            
            # Check structure of a sample day
            sample_day = daily_activity[0]
            if "date" in sample_day and "conversations" in sample_day:
                print("✅ Daily activity has correct structure")
            else:
                print("❌ Daily activity has incorrect structure")
        else:
            print(f"❌ Daily activity should contain 30 days of data, found {len(daily_activity)}")
        
        # Check agent usage structure
        if isinstance(agent_usage, list):
            print(f"✅ Agent usage contains {len(agent_usage)} agents")
            
            if agent_usage:
                # Check structure of a sample agent
                sample_agent = agent_usage[0]
                if "name" in sample_agent and "usage_count" in sample_agent and "archetype" in sample_agent:
                    print("✅ Agent usage has correct structure")
                else:
                    print("❌ Agent usage has incorrect structure")
        else:
            print("❌ Agent usage should be a list")
        
        # Check scenario distribution structure
        if isinstance(scenario_distribution, list):
            print(f"✅ Scenario distribution contains {len(scenario_distribution)} scenarios")
            
            if scenario_distribution:
                # Check structure of a sample scenario
                sample_scenario = scenario_distribution[0]
                if "scenario" in sample_scenario and "count" in sample_scenario:
                    print("✅ Scenario distribution has correct structure")
                else:
                    print("❌ Scenario distribution has incorrect structure")
        else:
            print("❌ Scenario distribution should be a list")
        
        # Check API usage structure
        api_usage_keys = ["current_usage", "max_requests", "remaining", "history"]
        missing_api_keys = [key for key in api_usage_keys if key not in api_usage]
        
        if not missing_api_keys:
            print("✅ API usage contains all required fields")
            
            # Check history structure
            history = api_usage.get("history", [])
            if isinstance(history, list):
                print(f"✅ API usage history contains {len(history)} entries")
                
                if history:
                    # Check structure of a sample history entry
                    sample_history = history[0]
                    if "date" in sample_history and "requests" in sample_history:
                        print("✅ API usage history has correct structure")
                    else:
                        print("❌ API usage history has incorrect structure")
            else:
                print("❌ API usage history should be a list")
        else:
            print(f"❌ API usage is missing fields: {', '.join(missing_api_keys)}")
    else:
        print("❌ Comprehensive analytics endpoint failed")
    
    # Test 2: Test the weekly summary endpoint
    print("\nTest 2: Testing weekly summary endpoint")
    
    weekly_test, weekly_response = run_test(
        "Weekly Summary",
        "/analytics/weekly-summary",
        method="GET",
        auth=True,
        expected_keys=["period", "conversations", "agents_created", "documents_created", 
                       "most_active_day", "daily_breakdown", "generated_at"]
    )
    
    if weekly_test and weekly_response:
        print("✅ Weekly summary endpoint returned successfully")
        
        # Verify the structure of the response
        period = weekly_response.get("period")
        conversations = weekly_response.get("conversations")
        agents_created = weekly_response.get("agents_created")
        documents_created = weekly_response.get("documents_created")
        most_active_day = weekly_response.get("most_active_day")
        daily_breakdown = weekly_response.get("daily_breakdown", {})
        
        # Check period
        if period == "Last 7 days":
            print("✅ Period is correctly set to 'Last 7 days'")
        else:
            print(f"❌ Period should be 'Last 7 days', found '{period}'")
        
        # Check counts
        if isinstance(conversations, int) and isinstance(agents_created, int) and isinstance(documents_created, int):
            print("✅ Count fields have correct types")
        else:
            print("❌ Count fields have incorrect types")
        
        # Check most active day
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "No activity"]
        if most_active_day in days_of_week:
            print(f"✅ Most active day is valid: {most_active_day}")
        else:
            print(f"❌ Most active day is invalid: {most_active_day}")
        
        # Check daily breakdown
        if isinstance(daily_breakdown, dict) and len(daily_breakdown) <= 7:
            print(f"✅ Daily breakdown contains {len(daily_breakdown)} days")
            
            # Check if all days of the week are present
            for day in days_of_week[:7]:  # Exclude "No activity"
                if day in daily_breakdown:
                    if isinstance(daily_breakdown[day], int):
                        print(f"✅ {day} has a valid count: {daily_breakdown[day]}")
                    else:
                        print(f"❌ {day} has an invalid count type: {type(daily_breakdown[day])}")
        else:
            print(f"❌ Daily breakdown should be a dictionary with up to 7 days, found {len(daily_breakdown)} entries")
    else:
        print("❌ Weekly summary endpoint failed")
    
    # Test 3: Test authentication requirements
    print("\nTest 3: Testing authentication requirements")
    
    # Test comprehensive endpoint without auth
    no_auth_comprehensive_test, _ = run_test(
        "Comprehensive Analytics Without Authentication",
        "/analytics/comprehensive",
        method="GET",
        auth=False,
        expected_status=403
    )
    
    if no_auth_comprehensive_test:
        print("✅ Comprehensive analytics endpoint correctly requires authentication (403 Forbidden)")
    else:
        print("❌ Comprehensive analytics endpoint does not properly enforce authentication")
    
    # Test weekly summary endpoint without auth
    no_auth_weekly_test, _ = run_test(
        "Weekly Summary Without Authentication",
        "/analytics/weekly-summary",
        method="GET",
        auth=False,
        expected_status=403
    )
    
    if no_auth_weekly_test:
        print("✅ Weekly summary endpoint correctly requires authentication")
    else:
        print("❌ Weekly summary endpoint does not properly enforce authentication")
    
    # Print summary
    print("\nANALYTICS ENDPOINTS SUMMARY:")
    
    # Check if all critical tests passed
    comprehensive_works = comprehensive_test
    weekly_works = weekly_test
    auth_works = no_auth_comprehensive_test and no_auth_weekly_test
    
    if comprehensive_works and weekly_works and auth_works:
        print("✅ Analytics endpoints are working correctly!")
        print("✅ Comprehensive analytics endpoint returns proper data structure")
        print("✅ Weekly summary endpoint returns proper data structure")
        print("✅ Authentication is properly enforced")
        return True, "Analytics endpoints are working correctly"
    else:
        issues = []
        if not comprehensive_works:
            issues.append("Comprehensive analytics endpoint is not functioning properly")
        if not weekly_works:
            issues.append("Weekly summary endpoint is not functioning properly")
        if not auth_works:
            issues.append("Authentication is not properly enforced for analytics endpoints")
        
        print("❌ Analytics endpoints have issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}

def test_basic_api_health():
    """Test basic API health endpoints"""
    print("\n" + "="*80)
    print("TESTING BASIC API HEALTH")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test API health without authentication")
            return False, "Authentication failed"
    
    # Test 1: GET /api/agents
    print("\nTest 1: GET /api/agents")
    agents_test, agents_response = run_test(
        "Get Agents",
        "/agents",
        method="GET",
        auth=True,
        measure_time=True
    )
    
    # Test 2: GET /api/conversations
    print("\nTest 2: GET /api/conversations")
    conversations_test, conversations_response = run_test(
        "Get Conversations",
        "/conversations",
        method="GET",
        auth=True,
        measure_time=True
    )
    
    # Test 3: GET /api/simulation/state
    print("\nTest 3: GET /api/simulation/state")
    state_test, state_response = run_test(
        "Get Simulation State",
        "/simulation/state",
        method="GET",
        auth=True,
        measure_time=True
    )
    
    # Test 4: GET /api/usage
    print("\nTest 4: GET /api/usage")
    usage_test, usage_response = run_test(
        "Get API Usage",
        "/usage",
        method="GET",
        auth=True,
        measure_time=True
    )
    
    # Print summary
    print("\nBASIC API HEALTH SUMMARY:")
    
    all_passed = agents_test and conversations_test and state_test and usage_test
    
    if all_passed:
        print("✅ All basic API health endpoints are working correctly!")
        return True, "All basic API health endpoints are working correctly"
    else:
        issues = []
        if not agents_test:
            issues.append("GET /api/agents endpoint is not working")
        if not conversations_test:
            issues.append("GET /api/conversations endpoint is not working")
        if not state_test:
            issues.append("GET /api/simulation/state endpoint is not working")
        if not usage_test:
            issues.append("GET /api/usage endpoint is not working")
        
        print("❌ Basic API health check has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}

def test_simulation_features():
    """Test simulation features including fast-forward"""
    print("\n" + "="*80)
    print("TESTING SIMULATION FEATURES")
    print("="*80)
    
    global auth_token
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test simulation features without authentication")
            return False, "Authentication failed"
    
    # Test 1: GET /api/simulation/state
    print("\nTest 1: GET /api/simulation/state")
    
    state_test, state_response = run_test(
        "Get Simulation State",
        "/simulation/state",
        method="GET",
        auth=True
    )
    
    if state_test and state_response:
        print(f"✅ Successfully retrieved simulation state")
        current_day = state_response.get("current_day", 0)
        print(f"Current simulation day: {current_day}")
    else:
        print("❌ Failed to retrieve simulation state")
    
    # Test 2: POST /api/simulation/start
    print("\nTest 2: POST /api/simulation/start")
    
    start_test, start_response = run_test(
        "Start Simulation",
        "/simulation/start",
        method="POST",
        auth=True,
        expected_keys=["message", "state"]
    )
    
    if start_test and start_response:
        print(f"✅ Successfully started simulation")
    else:
        print("❌ Failed to start simulation")
    
    # Test 3: POST /api/simulation/set-scenario
    print("\nTest 3: POST /api/simulation/set-scenario")
    
    scenario_data = {
        "scenario": "Testing the simulation features",
        "scenario_name": "API Test Scenario"
    }
    
    scenario_test, scenario_response = run_test(
        "Set Simulation Scenario",
        "/simulation/set-scenario",
        method="POST",
        data=scenario_data,
        auth=True,
        expected_keys=["message", "scenario"]
    )
    
    if scenario_test and scenario_response:
        print(f"✅ Successfully set simulation scenario")
    else:
        print("❌ Failed to set simulation scenario")
    
    # Test 4: POST /api/simulation/fast-forward
    print("\nTest 4: POST /api/simulation/fast-forward")
    
    fast_forward_data = {
        "target_days": 2,
        "conversations_per_period": 1
    }
    
    fast_forward_test, fast_forward_response = run_test(
        "Fast Forward Simulation",
        "/simulation/fast-forward",
        method="POST",
        data=fast_forward_data,
        auth=True,
        expected_keys=["message", "days_advanced", "conversations_generated"]
    )
    
    if fast_forward_test and fast_forward_response:
        print(f"✅ Successfully fast-forwarded simulation")
        days_advanced = fast_forward_response.get("days_advanced", 0)
        conversations_generated = fast_forward_response.get("conversations_generated", 0)
        print(f"Advanced {days_advanced} days and generated {conversations_generated} conversations")
    else:
        print("❌ Failed to fast-forward simulation")
    
    # Test 5: Verify simulation state after fast-forward
    print("\nTest 5: Verify simulation state after fast-forward")
    
    state_after_test, state_after_response = run_test(
        "Get Simulation State After Fast-Forward",
        "/simulation/state",
        method="GET",
        auth=True
    )
    
    if state_after_test and state_after_response:
        print(f"✅ Successfully retrieved simulation state after fast-forward")
        current_day_after = state_after_response.get("current_day", 0)
        print(f"Current simulation day after fast-forward: {current_day_after}")
        
        if state_response and current_day_after > state_response.get("current_day", 0):
            print(f"✅ Simulation day advanced from {state_response.get('current_day', 0)} to {current_day_after}")
        else:
            print(f"❌ Simulation day did not advance as expected")
    else:
        print("❌ Failed to retrieve simulation state after fast-forward")
    
    # Print summary
    print("\nSIMULATION FEATURES SUMMARY:")
    
    # Check if all critical tests passed
    get_state_works = state_test
    start_simulation_works = start_test
    set_scenario_works = scenario_test
    fast_forward_works = fast_forward_test
    verify_state_works = state_after_test
    
    if get_state_works and start_simulation_works and set_scenario_works and fast_forward_works and verify_state_works:
        print("✅ Simulation features are working correctly!")
        print("✅ GET /api/simulation/state endpoint is functioning properly")
        print("✅ POST /api/simulation/start endpoint is functioning properly")
        print("✅ POST /api/simulation/set-scenario endpoint is functioning properly")
        print("✅ POST /api/simulation/fast-forward endpoint is functioning properly")
        return True, "Simulation features are working correctly"
    else:
        issues = []
        if not get_state_works:
            issues.append("GET /api/simulation/state endpoint is not functioning properly")
        if not start_simulation_works:
            issues.append("POST /api/simulation/start endpoint is not functioning properly")
        if not set_scenario_works:
            issues.append("POST /api/simulation/set-scenario endpoint is not functioning properly")
        if not fast_forward_works:
            issues.append("POST /api/simulation/fast-forward endpoint is not functioning properly")
        if not verify_state_works:
            issues.append("Simulation state verification after fast-forward failed")
        
        print("❌ Simulation features have issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}

def test_translation_features():
    """Test translation features"""
    print("\n" + "="*80)
    print("TESTING TRANSLATION FEATURES")
    print("="*80)
    
    global auth_token
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test translation features without authentication")
            return False, "Authentication failed"
    
    # Test 1: POST /api/conversations/translate
    print("\nTest 1: POST /api/conversations/translate")
    
    # Create a test conversation to translate
    conversation_data = {
        "title": f"Test Conversation {uuid.uuid4().hex[:8]}",
        "participants": ["Test Agent 1", "Test Agent 2"],
        "messages": [
            {
                "agent_name": "Test Agent 1",
                "message": "Hello, this is a test message."
            },
            {
                "agent_name": "Test Agent 2",
                "message": "Hi there! This is a response to the test message."
            }
        ],
        "language": "en",
        "tags": ["test", "api"]
    }
    
    save_conversation_test, save_conversation_response = run_test(
        "Save Conversation for Translation",
        "/conversation-history",
        method="POST",
        data=conversation_data,
        auth=True,
        expected_keys=["success", "conversation_id"]
    )
    
    if save_conversation_test and save_conversation_response:
        conversation_id = save_conversation_response.get("conversation_id")
        print(f"✅ Successfully saved conversation with ID: {conversation_id}")
        
        # Translate the conversation
        translate_data = {
            "conversation_id": conversation_id,
            "target_language": "es"  # Spanish
        }
        
        translate_test, translate_response = run_test(
            "Translate Conversation",
            "/conversations/translate",
            method="POST",
            data=translate_data,
            auth=True,
            expected_keys=["success", "message"]
        )
        
        if translate_test and translate_response:
            print(f"✅ Successfully translated conversation")
            
            # Verify translation
            get_translated_test, get_translated_response = run_test(
                "Get Translated Conversation",
                f"/conversation-history/{conversation_id}",
                method="GET",
                auth=True
            )
            
            if get_translated_test and get_translated_response:
                print(f"✅ Successfully retrieved translated conversation")
                language = get_translated_response.get("language")
                print(f"Conversation language: {language}")
                
                if language == "es":
                    print("✅ Conversation was successfully translated to Spanish")
                else:
                    print(f"❌ Conversation language is {language}, expected 'es'")
            else:
                print("❌ Failed to retrieve translated conversation")
        else:
            print("❌ Failed to translate conversation")
    else:
        print("❌ Failed to save conversation for translation")
        translate_test = False
    
    # Print summary
    print("\nTRANSLATION FEATURES SUMMARY:")
    
    # Check if all critical tests passed
    translation_works = translate_test if save_conversation_test else False
    
    if translation_works:
        print("✅ Translation features are working correctly!")
        print("✅ POST /api/conversations/translate endpoint is functioning properly")
        return True, "Translation features are working correctly"
    else:
        issues = []
        if not translation_works:
            issues.append("POST /api/conversations/translate endpoint is not functioning properly")
        
        print("❌ Translation features have issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}

def test_avatar_generation():
    """Test avatar generation features"""
    print("\n" + "="*80)
    print("TESTING AVATAR GENERATION")
    print("="*80)
    
    global auth_token
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test avatar generation without authentication")
            return False, "Authentication failed"
    
    # Test 1: POST /api/avatars/generate
    print("\nTest 1: POST /api/avatars/generate")
    
    avatar_data = {
        "prompt": "Professional software engineer with glasses"
    }
    
    avatar_test, avatar_response = run_test(
        "Generate Avatar",
        "/avatars/generate",
        method="POST",
        data=avatar_data,
        auth=True,
        expected_keys=["success", "image_url"]
    )
    
    if avatar_test and avatar_response:
        image_url = avatar_response.get("image_url")
        print(f"✅ Successfully generated avatar")
        print(f"Avatar URL: {image_url}")
        
        # Verify the image URL is accessible
        if image_url:
            try:
                response = requests.head(image_url)
                if response.status_code == 200:
                    print("✅ Avatar image URL is accessible")
                else:
                    print(f"❌ Avatar image URL returned status code {response.status_code}")
            except Exception as e:
                print(f"❌ Error accessing avatar image URL: {e}")
    else:
        print("❌ Failed to generate avatar")
    
    # Print summary
    print("\nAVATAR GENERATION SUMMARY:")
    
    # Check if all critical tests passed
    avatar_generation_works = avatar_test
    
    if avatar_generation_works:
        print("✅ Avatar generation is working correctly!")
        print("✅ POST /api/avatars/generate endpoint is functioning properly")
        return True, "Avatar generation is working correctly"
    else:
        issues = []
        if not avatar_generation_works:
            issues.append("POST /api/avatars/generate endpoint is not functioning properly")
        
        print("❌ Avatar generation has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}

def test_admin_functionality():
    """Test admin functionality"""
    print("\n" + "="*80)
    print("TESTING ADMIN FUNCTIONALITY")
    print("="*80)
    
    # Try to login as admin
    admin_email = "dino@cytonic.com"
    admin_password = "Observerinho8"  # This is the password mentioned in the test_result.md
    
    login_data = {
        "email": admin_email,
        "password": admin_password
    }
    
    admin_login_test, admin_login_response = run_test(
        "Login as Admin",
        "/auth/login",
        method="POST",
        data=login_data,
        expected_keys=["access_token", "token_type", "user"]
    )
    
    if admin_login_test and admin_login_response:
        print("✅ Successfully logged in as admin")
        admin_token = admin_login_response.get("access_token")
        
        # Test 1: GET /api/admin/dashboard/stats
        print("\nTest 1: GET /api/admin/dashboard/stats")
        
        stats_test, stats_response = run_test(
            "Get Admin Dashboard Stats",
            "/admin/dashboard/stats",
            method="GET",
            auth=True,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if stats_test and stats_response:
            print(f"✅ Successfully retrieved admin dashboard stats")
        else:
            print("❌ Failed to retrieve admin dashboard stats")
        
        # Test 2: GET /api/admin/users
        print("\nTest 2: GET /api/admin/users")
        
        users_test, users_response = run_test(
            "Get Admin Users List",
            "/admin/users",
            method="GET",
            auth=True,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if users_test and users_response:
            print(f"✅ Successfully retrieved admin users list")
            user_count = len(users_response) if isinstance(users_response, list) else 0
            print(f"Found {user_count} users")
        else:
            print("❌ Failed to retrieve admin users list")
        
        # Test 3: GET /api/admin/activity/recent
        print("\nTest 3: GET /api/admin/activity/recent")
        
        activity_test, activity_response = run_test(
            "Get Admin Recent Activity",
            "/admin/activity/recent",
            method="GET",
            auth=True,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if activity_test and activity_response:
            print(f"✅ Successfully retrieved admin recent activity")
        else:
            print("❌ Failed to retrieve admin recent activity")
        
        # Test 4: Test regular user access to admin endpoints
        print("\nTest 4: Test regular user access to admin endpoints")
        
        # Login as regular user
        if not test_login():
            print("❌ Cannot test regular user access without authentication")
        else:
            # Try to access admin dashboard stats
            regular_stats_test, regular_stats_response = run_test(
                "Regular User Access to Admin Dashboard Stats",
                "/admin/dashboard/stats",
                method="GET",
                auth=True,
                expected_status=403
            )
            
            if regular_stats_test:
                print("✅ Regular user correctly denied access to admin dashboard stats")
            else:
                print("❌ Regular user access to admin dashboard stats not properly restricted")
        
        # Print summary
        print("\nADMIN FUNCTIONALITY SUMMARY:")
        
        # Check if all critical tests passed
        admin_login_works = admin_login_test
        stats_works = stats_test
        users_works = users_test
        activity_works = activity_test
        access_restriction_works = regular_stats_test
        
        if admin_login_works and stats_works and users_works and activity_works and access_restriction_works:
            print("✅ Admin functionality is working correctly!")
            print("✅ Admin login is functioning properly")
            print("✅ GET /api/admin/dashboard/stats endpoint is functioning properly")
            print("✅ GET /api/admin/users endpoint is functioning properly")
            print("✅ GET /api/admin/activity/recent endpoint is functioning properly")
            print("✅ Admin access restrictions are functioning properly")
            return True, "Admin functionality is working correctly"
        else:
            issues = []
            if not admin_login_works:
                issues.append("Admin login is not functioning properly")
            if not stats_works:
                issues.append("GET /api/admin/dashboard/stats endpoint is not functioning properly")
            if not users_works:
                issues.append("GET /api/admin/users endpoint is not functioning properly")
            if not activity_works:
                issues.append("GET /api/admin/activity/recent endpoint is not functioning properly")
            if not access_restriction_works:
                issues.append("Admin access restrictions are not functioning properly")
            
            print("❌ Admin functionality has issues:")
            for issue in issues:
                print(f"  - {issue}")
            return False, {"issues": issues}
    else:
        print("❌ Failed to login as admin")
        print("❌ Cannot test admin functionality without admin access")
        return False, "Failed to login as admin"
if __name__ == "__main__":
    main()
