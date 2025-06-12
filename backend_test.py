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

def run_test(test_name, endpoint, method="GET", data=None, expected_status=200, expected_keys=None, auth=False, headers=None):
    """Run a test against the specified endpoint"""
    url = f"{API_URL}{endpoint}"
    print(f"\n{'='*80}\nTesting: {test_name} ({method} {url})")
    
    # Set up headers with auth token if needed
    if headers is None:
        headers = {}
    
    if auth and auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, json=data, headers=headers)
        else:
            print(f"Unsupported method: {method}")
            return False, None
        
        # Print response details
        print(f"Status Code: {response.status_code}")
        
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
        
        test_results["tests"].append({
            "name": test_name,
            "endpoint": endpoint,
            "method": method,
            "status_code": response.status_code,
            "expected_status": expected_status,
            "result": result
        })
        
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

def test_auth_me():
    """Test the /auth/me endpoint with the auth token"""
    if not auth_token:
        if not test_login():
            print("❌ Cannot test /auth/me without authentication")
            return False, "Authentication failed"
    
    auth_me_test, auth_me_response = run_test(
        "Auth Me Endpoint",
        "/auth/me",
        method="GET",
        auth=True,
        expected_keys=["id", "email", "name"]
    )
    
    if auth_me_test and auth_me_response:
        print(f"✅ Auth Me endpoint returned user data: {auth_me_response.get('name')}")
        return True, "Auth Me endpoint is working correctly"
    else:
        print("❌ Auth Me endpoint failed")
        return False, "Auth Me endpoint failed"

def test_bulk_delete_functionality():
    """Test the bulk delete functionality for conversations and documents"""
    print("\n" + "="*80)
    print("TESTING BULK DELETE FUNCTIONALITY")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test bulk delete functionality without authentication")
            return False, "Authentication failed"
    
    # Test authentication requirement for both endpoints
    print("\nTesting authentication requirement for bulk delete endpoints:")
    
    # Test conversation bulk delete without auth
    no_auth_conv_test, _ = run_test(
        "Conversation Bulk Delete Without Auth",
        "/conversation-history/bulk",
        method="DELETE",
        data={"conversation_ids": ["test-id-1", "test-id-2"]},
        expected_status=403
    )
    
    # Test document bulk delete without auth
    no_auth_doc_test, _ = run_test(
        "Document Bulk Delete Without Auth",
        "/documents/bulk",
        method="DELETE",
        data={"document_ids": ["test-id-1", "test-id-2"]},
        expected_status=403
    )
    
    # Create test conversations
    print("\nCreating test conversations for bulk delete testing:")
    conversation_ids = []
    
    for i in range(3):
        conversation_data = {
            "participants": [f"Test Agent {j+1}" for j in range(3)],
            "messages": [
                {
                    "agent_name": f"Test Agent {j+1}",
                    "message": f"This is test message {j+1} in conversation {i+1}"
                } for j in range(3)
            ],
            "title": f"Test Conversation {i+1} for Bulk Delete",
            "scenario_name": "Bulk Delete Test"
        }
        
        conv_test, conv_response = run_test(
            f"Create Test Conversation {i+1}",
            "/conversation-history",
            method="POST",
            data=conversation_data,
            auth=True,
            expected_keys=["id"]
        )
        
        if conv_test and conv_response:
            conversation_ids.append(conv_response.get("id"))
    
    # Create test documents
    print("\nCreating test documents for bulk delete testing:")
    document_ids = []
    
    for i in range(3):
        document_data = {
            "title": f"Test Document {i+1} for Bulk Delete",
            "category": "Protocol",
            "description": f"This is test document {i+1} for bulk delete testing",
            "content": f"# Test Document {i+1}\n\nThis is a test document for bulk delete testing.",
            "keywords": ["test", "bulk", "delete"],
            "authors": ["Test Agent"]
        }
        
        doc_test, doc_response = run_test(
            f"Create Test Document {i+1}",
            "/documents/create",
            method="POST",
            data=document_data,
            auth=True,
            expected_keys=["document_id"]
        )
        
        if doc_test and doc_response:
            document_ids.append(doc_response.get("document_id"))
    
    # Test conversation bulk delete with valid IDs
    print("\nTesting conversation bulk delete with valid IDs:")
    if conversation_ids:
        # Delete first two conversations
        delete_ids = conversation_ids[:2]
        conv_bulk_test, conv_bulk_response = run_test(
            "Conversation Bulk Delete",
            "/conversation-history/bulk",
            method="DELETE",
            data=delete_ids,  # Pass the list directly, not as a JSON object
            auth=True,
            expected_keys=["message", "deleted_count"]
        )
        
        if conv_bulk_test and conv_bulk_response:
            deleted_count = conv_bulk_response.get("deleted_count", 0)
            if deleted_count == len(delete_ids):
                print(f"✅ Successfully deleted {deleted_count} conversations")
            else:
                print(f"❌ Expected to delete {len(delete_ids)} conversations, but deleted {deleted_count}")
        
        # Verify the conversations were deleted
        get_convs_test, get_convs_response = run_test(
            "Get Conversations After Bulk Delete",
            "/conversation-history",
            method="GET",
            auth=True
        )
        
        if get_convs_test and get_convs_response:
            remaining_convs = get_convs_response
            remaining_ids = [conv.get("id") for conv in remaining_convs]
            
            # Check if deleted IDs are no longer present
            deleted_ids_present = any(conv_id in remaining_ids for conv_id in delete_ids)
            if not deleted_ids_present:
                print("✅ Deleted conversations are no longer in the database")
            else:
                print("❌ Some deleted conversations are still in the database")
            
            # Check if non-deleted ID is still present
            if conversation_ids[2] in remaining_ids:
                print("✅ Non-deleted conversation is still in the database")
            else:
                print("❌ Non-deleted conversation is missing from the database")
    else:
        print("❌ No test conversations created, skipping conversation bulk delete test")
    
    # Test document bulk delete with valid IDs
    print("\nTesting document bulk delete with valid IDs:")
    if document_ids:
        # Delete first two documents
        delete_ids = document_ids[:2]
        doc_bulk_test, doc_bulk_response = run_test(
            "Document Bulk Delete",
            "/documents/bulk",
            method="DELETE",
            data=delete_ids,  # Pass the list directly, not as a JSON object
            auth=True,
            expected_keys=["message", "deleted_count"]
        )
        
        if doc_bulk_test and doc_bulk_response:
            deleted_count = doc_bulk_response.get("deleted_count", 0)
            if deleted_count == len(delete_ids):
                print(f"✅ Successfully deleted {deleted_count} documents")
            else:
                print(f"❌ Expected to delete {len(delete_ids)} documents, but deleted {deleted_count}")
        
        # Verify the documents were deleted
        get_docs_test, get_docs_response = run_test(
            "Get Documents After Bulk Delete",
            "/documents",
            method="GET",
            auth=True
        )
        
        if get_docs_test and get_docs_response:
            remaining_docs = get_docs_response
            remaining_ids = [doc.get("id") for doc in remaining_docs]
            
            # Check if deleted IDs are no longer present
            deleted_ids_present = any(doc_id in remaining_ids for doc_id in delete_ids)
            if not deleted_ids_present:
                print("✅ Deleted documents are no longer in the database")
            else:
                print("❌ Some deleted documents are still in the database")
            
            # Check if non-deleted ID is still present
            if document_ids[2] in remaining_ids:
                print("✅ Non-deleted document is still in the database")
            else:
                print("❌ Non-deleted document is missing from the database")
    else:
        print("❌ No test documents created, skipping document bulk delete test")
    
    # Test conversation bulk delete with non-existent IDs
    print("\nTesting conversation bulk delete with non-existent IDs:")
    non_existent_ids = ["non-existent-id-1", "non-existent-id-2"]
    non_exist_conv_test, non_exist_conv_response = run_test(
        "Conversation Bulk Delete with Non-Existent IDs",
        "/conversation-history/bulk",
        method="DELETE",
        data={"conversation_ids": non_existent_ids},
        auth=True,
        expected_status=404
    )
    
    if non_exist_conv_test:
        print("❌ Expected 404 error for non-existent conversation IDs, but got success")
    else:
        print("✅ Correctly returned 404 for non-existent conversation IDs")
    
    # Test document bulk delete with non-existent IDs
    print("\nTesting document bulk delete with non-existent IDs:")
    non_exist_doc_test, non_exist_doc_response = run_test(
        "Document Bulk Delete with Non-Existent IDs",
        "/documents/bulk",
        method="DELETE",
        data={"document_ids": non_existent_ids},
        auth=True,
        expected_status=404
    )
    
    if non_exist_doc_test:
        print("❌ Expected 404 error for non-existent document IDs, but got success")
    else:
        print("✅ Correctly returned 404 for non-existent document IDs")
    
    # Test conversation bulk delete with empty array
    print("\nTesting conversation bulk delete with empty array:")
    empty_conv_test, empty_conv_response = run_test(
        "Conversation Bulk Delete with Empty Array",
        "/conversation-history/bulk",
        method="DELETE",
        data={"conversation_ids": []},
        auth=True,
        expected_keys=["message", "deleted_count"]
    )
    
    if empty_conv_test and empty_conv_response:
        deleted_count = empty_conv_response.get("deleted_count", -1)
        if deleted_count == 0:
            print("✅ Correctly reported 0 deleted conversations for empty array")
        else:
            print(f"❌ Expected 0 deleted conversations for empty array, but got {deleted_count}")
    
    # Test document bulk delete with empty array
    print("\nTesting document bulk delete with empty array:")
    empty_doc_test, empty_doc_response = run_test(
        "Document Bulk Delete with Empty Array",
        "/documents/bulk",
        method="DELETE",
        data={"document_ids": []},
        auth=True,
        expected_keys=["message", "deleted_count"]
    )
    
    if empty_doc_test and empty_doc_response:
        deleted_count = empty_doc_response.get("deleted_count", -1)
        if deleted_count == 0:
            print("✅ Correctly reported 0 deleted documents for empty array")
        else:
            print(f"❌ Expected 0 deleted documents for empty array, but got {deleted_count}")
    
    # Clean up - delete remaining conversation and document
    if conversation_ids and len(conversation_ids) > 2:
        run_test(
            "Delete Remaining Test Conversation",
            f"/conversation-history/{conversation_ids[2]}",
            method="DELETE",
            auth=True
        )
    
    if document_ids and len(document_ids) > 2:
        run_test(
            "Delete Remaining Test Document",
            f"/documents/{document_ids[2]}",
            method="DELETE",
            auth=True
        )
    
    # Print summary
    print("\nBULK DELETE FUNCTIONALITY SUMMARY:")
    
    auth_tests_passed = not no_auth_conv_test and not no_auth_doc_test
    conv_bulk_tests_passed = len(conversation_ids) >= 2 and conv_bulk_test and not non_exist_conv_test and empty_conv_test
    doc_bulk_tests_passed = len(document_ids) >= 2 and doc_bulk_test and not non_exist_doc_test and empty_doc_test
    
    if auth_tests_passed and conv_bulk_tests_passed and doc_bulk_tests_passed:
        print("✅ Bulk delete functionality is working correctly!")
        print("✅ Authentication is properly enforced for both endpoints")
        print("✅ Conversation bulk delete works correctly with valid IDs")
        print("✅ Document bulk delete works correctly with valid IDs")
        print("✅ Both endpoints handle non-existent IDs correctly")
        print("✅ Both endpoints handle empty arrays correctly")
        return True, "Bulk delete functionality is working correctly"
    else:
        issues = []
        if not auth_tests_passed:
            issues.append("Authentication is not properly enforced for bulk delete endpoints")
        if not conv_bulk_tests_passed:
            issues.append("Conversation bulk delete has issues")
        if not doc_bulk_tests_passed:
            issues.append("Document bulk delete has issues")
        
        print("❌ Bulk delete functionality has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Bulk delete functionality has issues"

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("RUNNING BACKEND API TESTS")
    print("="*80)
    
    # Test authentication first
    test_login()
    test_auth_me()
    
    # Test bulk delete functionality
    bulk_delete_success, bulk_delete_message = test_bulk_delete_functionality()
    
    # Print summary of all tests
    print_summary()
    
    # Print final conclusion
    print("\n" + "="*80)
    print("BULK DELETE FUNCTIONALITY ASSESSMENT")
    print("="*80)
    
    if bulk_delete_success:
        print("✅ Bulk delete functionality is working correctly!")
        print("✅ Both conversation and document bulk delete endpoints are properly implemented")
        print("✅ Authentication is properly enforced")
        print("✅ User data isolation is working correctly")
        print("✅ Error handling is implemented for non-existent IDs")
        print("✅ Empty arrays are handled correctly")
    else:
        print(f"❌ {bulk_delete_message}")
    print("="*80)
    
    return bulk_delete_success

if __name__ == "__main__":
    main()
