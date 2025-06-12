#!/usr/bin/env python3
import requests
import json
import time
import os
import sys
from dotenv import load_dotenv
import uuid

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

def test_conversation_bulk_delete():
    """Test the conversation bulk delete functionality"""
    print("\n" + "="*80)
    print("TESTING CONVERSATION BULK DELETE")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test conversation bulk delete without authentication")
            return False, "Authentication failed"
    
    # Get existing conversations
    get_conversations_test, get_conversations_response = run_test(
        "Get Conversation History",
        "/conversation-history",
        method="GET",
        auth=True
    )
    
    existing_conversation_ids = []
    if get_conversations_test and isinstance(get_conversations_response, list):
        for conversation in get_conversations_response:
            if "id" in conversation:
                existing_conversation_ids.append(conversation["id"])
        
        print(f"✅ Found {len(existing_conversation_ids)} existing conversations")
    
    # Create test conversations if needed
    conversation_ids = []
    if len(existing_conversation_ids) >= 3:
        # Use existing conversations
        conversation_ids = existing_conversation_ids[:3]
        print(f"✅ Using {len(conversation_ids)} existing conversations for testing")
    else:
        # Create new conversations
        for i in range(3):
            conversation_data = {
                "simulation_id": f"test-simulation-{uuid.uuid4()}",
                "participants": [f"Test Agent {j+1}" for j in range(3)],
                "messages": [
                    {
                        "agent_id": f"agent-{j+1}",
                        "agent_name": f"Test Agent {j+1}",
                        "message": f"This is test message {j+1} in conversation {i+1}",
                        "mood": "neutral"
                    } for j in range(3)
                ],
                "title": f"Test Conversation {i+1}",
                "tags": ["test", "bulk-delete"]
            }
            
            create_test, create_response = run_test(
                f"Create Test Conversation {i+1}",
                "/conversation-history",
                method="POST",
                data=conversation_data,
                auth=True,
                expected_keys=["message"]
            )
            
            if create_test:
                # Get the conversation history again to find our new conversation
                time.sleep(1)  # Wait a moment for the database to update
                get_updated_test, get_updated_response = run_test(
                    f"Get Updated Conversation History {i+1}",
                    "/conversation-history",
                    method="GET",
                    auth=True
                )
                
                if get_updated_test and isinstance(get_updated_response, list):
                    # Find the conversation with our title
                    for conversation in get_updated_response:
                        if conversation.get("title") == f"Test Conversation {i+1}":
                            conversation_ids.append(conversation["id"])
                            print(f"✅ Created conversation with ID: {conversation['id']}")
                            break
    
    if len(conversation_ids) < 2:
        print("❌ Failed to create or find enough test conversations")
        return False, "Failed to create or find test conversations"
    
    # Test bulk delete with valid conversation IDs
    # Create a custom endpoint with the IDs in the URL
    ids_param = ",".join(conversation_ids)
    bulk_delete_endpoint = f"/conversation-history/bulk?ids={ids_param}"
    
    bulk_delete_test, bulk_delete_response = run_test(
        "Bulk Delete Conversations",
        bulk_delete_endpoint,
        method="DELETE",
        auth=True,
        expected_keys=["message", "deleted_count"]
    )
    
    if bulk_delete_test and bulk_delete_response:
        deleted_count = bulk_delete_response.get("deleted_count", 0)
        if deleted_count == len(conversation_ids):
            print(f"✅ Successfully deleted {deleted_count} conversations")
        else:
            print(f"❌ Expected to delete {len(conversation_ids)} conversations, but deleted {deleted_count}")
            return False, f"Expected to delete {len(conversation_ids)} conversations, but deleted {deleted_count}"
    else:
        print("❌ Bulk delete conversations failed")
        return False, "Bulk delete conversations failed"
    
    # Test bulk delete with non-existent conversation IDs
    non_existent_ids = [str(uuid.uuid4()) for _ in range(2)]
    non_existent_endpoint = f"/conversation-history/bulk?ids={','.join(non_existent_ids)}"
    
    non_existent_test, non_existent_response = run_test(
        "Bulk Delete Non-existent Conversations",
        non_existent_endpoint,
        method="DELETE",
        auth=True,
        expected_status=404
    )
    
    if non_existent_test:
        print("✅ Correctly handled non-existent conversation IDs")
    else:
        print("❌ Failed to handle non-existent conversation IDs correctly")
    
    # Test bulk delete with empty array
    empty_test, empty_response = run_test(
        "Bulk Delete Empty Conversation Array",
        "/conversation-history/bulk?ids=",
        method="DELETE",
        auth=True,
        expected_keys=["message", "deleted_count"]
    )
    
    if empty_test and empty_response.get("deleted_count", -1) == 0:
        print("✅ Correctly handled empty conversation ID array")
    else:
        print("❌ Failed to handle empty conversation ID array correctly")
    
    # Test bulk delete without authentication
    no_auth_test, no_auth_response = run_test(
        "Bulk Delete Conversations Without Auth",
        f"/conversation-history/bulk?ids={str(uuid.uuid4())}",
        method="DELETE",
        expected_status=403
    )
    
    if no_auth_test:
        print("✅ Correctly rejected unauthenticated bulk delete request")
    else:
        print("❌ Failed to reject unauthenticated bulk delete request")
    
    # Print summary
    print("\nCONVERSATION BULK DELETE SUMMARY:")
    
    if bulk_delete_test and non_existent_test and empty_test and no_auth_test:
        print("✅ Conversation bulk delete functionality is working correctly!")
        return True, "Conversation bulk delete functionality is working correctly"
    else:
        issues = []
        if not bulk_delete_test:
            issues.append("Bulk delete with valid IDs failed")
        if not non_existent_test:
            issues.append("Handling of non-existent IDs failed")
        if not empty_test:
            issues.append("Handling of empty ID array failed")
        if not no_auth_test:
            issues.append("Authentication check failed")
        
        print("❌ Conversation bulk delete functionality has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Conversation bulk delete functionality has issues"

def test_document_bulk_delete():
    """Test the document bulk delete functionality"""
    print("\n" + "="*80)
    print("TESTING DOCUMENT BULK DELETE")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test document bulk delete without authentication")
            return False, "Authentication failed"
    
    # Create test documents
    document_ids = []
    for i in range(3):
        document_data = {
            "title": f"Test Document {i+1}",
            "category": "Protocol",
            "description": f"This is test document {i+1} for bulk delete testing",
            "content": f"# Test Document {i+1}\n\n## Purpose\nThis is a test document created for bulk delete testing.\n\n## Procedure\n1. Step one\n2. Step two\n3. Step three",
            "keywords": ["test", "bulk-delete"],
            "authors": ["Test User"]
        }
        
        create_test, create_response = run_test(
            f"Create Test Document {i+1}",
            "/documents/create",
            method="POST",
            data=document_data,
            auth=True,
            expected_keys=["success", "document_id"]
        )
        
        if create_test and create_response:
            document_id = create_response.get("document_id")
            if document_id:
                document_ids.append(document_id)
                print(f"✅ Created document with ID: {document_id}")
    
    if len(document_ids) < 2:
        print("❌ Failed to create enough test documents")
        return False, "Failed to create test documents"
    
    # Test bulk delete with valid document IDs
    # Create a custom endpoint with the IDs in the URL
    ids_param = ",".join(document_ids)
    bulk_delete_endpoint = f"/documents/bulk?ids={ids_param}"
    
    bulk_delete_test, bulk_delete_response = run_test(
        "Bulk Delete Documents",
        bulk_delete_endpoint,
        method="DELETE",
        auth=True,
        expected_keys=["message", "deleted_count"]
    )
    
    if bulk_delete_test and bulk_delete_response:
        deleted_count = bulk_delete_response.get("deleted_count", 0)
        if deleted_count == len(document_ids):
            print(f"✅ Successfully deleted {deleted_count} documents")
        else:
            print(f"❌ Expected to delete {len(document_ids)} documents, but deleted {deleted_count}")
            return False, f"Expected to delete {len(document_ids)} documents, but deleted {deleted_count}"
    else:
        print("❌ Bulk delete documents failed")
        return False, "Bulk delete documents failed"
    
    # Test bulk delete with non-existent document IDs
    non_existent_ids = [str(uuid.uuid4()) for _ in range(2)]
    non_existent_endpoint = f"/documents/bulk?ids={','.join(non_existent_ids)}"
    
    non_existent_test, non_existent_response = run_test(
        "Bulk Delete Non-existent Documents",
        non_existent_endpoint,
        method="DELETE",
        auth=True,
        expected_status=404
    )
    
    if non_existent_test:
        print("✅ Correctly handled non-existent document IDs")
    else:
        print("❌ Failed to handle non-existent document IDs correctly")
    
    # Test bulk delete with empty array
    empty_test, empty_response = run_test(
        "Bulk Delete Empty Document Array",
        "/documents/bulk?ids=",
        method="DELETE",
        auth=True,
        expected_keys=["message", "deleted_count"]
    )
    
    if empty_test and empty_response.get("deleted_count", -1) == 0:
        print("✅ Correctly handled empty document ID array")
    else:
        print("❌ Failed to handle empty document ID array correctly")
    
    # Test bulk delete without authentication
    no_auth_test, no_auth_response = run_test(
        "Bulk Delete Documents Without Auth",
        f"/documents/bulk?ids={str(uuid.uuid4())}",
        method="DELETE",
        expected_status=403
    )
    
    if no_auth_test:
        print("✅ Correctly rejected unauthenticated bulk delete request")
    else:
        print("❌ Failed to reject unauthenticated bulk delete request")
    
    # Print summary
    print("\nDOCUMENT BULK DELETE SUMMARY:")
    
    if bulk_delete_test and non_existent_test and empty_test and no_auth_test:
        print("✅ Document bulk delete functionality is working correctly!")
        return True, "Document bulk delete functionality is working correctly"
    else:
        issues = []
        if not bulk_delete_test:
            issues.append("Bulk delete with valid IDs failed")
        if not non_existent_test:
            issues.append("Handling of non-existent IDs failed")
        if not empty_test:
            issues.append("Handling of empty ID array failed")
        if not no_auth_test:
            issues.append("Authentication check failed")
        
        print("❌ Document bulk delete functionality has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Document bulk delete functionality has issues"

def test_mixed_ownership():
    """Test bulk delete with mixed ownership (some IDs belonging to other users)"""
    print("\n" + "="*80)
    print("TESTING BULK DELETE WITH MIXED OWNERSHIP")
    print("="*80)
    
    # This test is theoretical since we can't create documents for other users in this test environment
    # We'll simulate by using non-existent IDs which should have the same effect
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test mixed ownership without authentication")
            return False, "Authentication failed"
    
    # Create one valid document
    document_data = {
        "title": "Valid Document",
        "category": "Protocol",
        "description": "This is a valid document for mixed ownership testing",
        "content": "# Valid Document\n\n## Purpose\nThis is a valid document created for mixed ownership testing.\n\n## Procedure\n1. Step one\n2. Step two\n3. Step three",
        "keywords": ["test", "mixed-ownership"],
        "authors": ["Test User"]
    }
    
    create_test, create_response = run_test(
        "Create Valid Document",
        "/documents/create",
        method="POST",
        data=document_data,
        auth=True,
        expected_keys=["success", "document_id"]
    )
    
    valid_document_id = None
    if create_test and create_response:
        valid_document_id = create_response.get("document_id")
        if valid_document_id:
            print(f"✅ Created valid document with ID: {valid_document_id}")
    
    if not valid_document_id:
        print("❌ Failed to create valid document")
        return False, "Failed to create valid document"
    
    # Test bulk delete with mixed valid and "other user" (non-existent) IDs
    other_user_ids = [str(uuid.uuid4()) for _ in range(2)]
    mixed_ids = [valid_document_id] + other_user_ids
    mixed_endpoint = f"/documents/bulk?ids={','.join(mixed_ids)}"
    
    mixed_test, mixed_response = run_test(
        "Bulk Delete Mixed Ownership Documents",
        mixed_endpoint,
        method="DELETE",
        auth=True,
        expected_status=404
    )
    
    if mixed_test:
        print("✅ Correctly rejected bulk delete with mixed ownership")
    else:
        print("❌ Failed to handle mixed ownership correctly")
    
    # Clean up - delete the valid document if it still exists
    if valid_document_id:
        run_test(
            "Delete Valid Document",
            f"/documents/{valid_document_id}",
            method="DELETE",
            auth=True
        )
    
    # Print summary
    print("\nMIXED OWNERSHIP BULK DELETE SUMMARY:")
    
    if mixed_test:
        print("✅ Mixed ownership handling is working correctly!")
        return True, "Mixed ownership handling is working correctly"
    else:
        print("❌ Mixed ownership handling has issues")
        return False, "Mixed ownership handling has issues"

def test_invalid_token():
    """Test bulk delete with invalid token"""
    print("\n" + "="*80)
    print("TESTING BULK DELETE WITH INVALID TOKEN")
    print("="*80)
    
    # Test with invalid token
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpbnZhbGlkLXVzZXItaWQiLCJleHAiOjE5MDAwMDAwMDB9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    
    headers = {"Authorization": f"Bearer {invalid_token}"}
    
    # Test conversation bulk delete with invalid token
    conv_invalid_test, conv_invalid_response = run_test(
        "Conversation Bulk Delete with Invalid Token",
        "/conversation-history/bulk?ids=123,456",
        method="DELETE",
        expected_status=401,
        headers=headers
    )
    
    if conv_invalid_test:
        print("✅ Correctly rejected conversation bulk delete with invalid token")
    else:
        print("❌ Failed to reject conversation bulk delete with invalid token")
    
    # Test document bulk delete with invalid token
    doc_invalid_test, doc_invalid_response = run_test(
        "Document Bulk Delete with Invalid Token",
        "/documents/bulk?ids=123,456",
        method="DELETE",
        expected_status=401,
        headers=headers
    )
    
    if doc_invalid_test:
        print("✅ Correctly rejected document bulk delete with invalid token")
    else:
        print("❌ Failed to reject document bulk delete with invalid token")
    
    # Print summary
    print("\nINVALID TOKEN BULK DELETE SUMMARY:")
    
    if conv_invalid_test and doc_invalid_test:
        print("✅ Invalid token handling is working correctly!")
        return True, "Invalid token handling is working correctly"
    else:
        issues = []
        if not conv_invalid_test:
            issues.append("Conversation bulk delete with invalid token not rejected properly")
        if not doc_invalid_test:
            issues.append("Document bulk delete with invalid token not rejected properly")
        
        print("❌ Invalid token handling has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Invalid token handling has issues"

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("RUNNING BULK DELETE API TESTS")
    print("="*80)
    
    # Test authentication first
    test_login()
    test_auth_me()
    
    # Test conversation bulk delete
    conv_bulk_delete_success, conv_bulk_delete_message = test_conversation_bulk_delete()
    
    # Test document bulk delete
    doc_bulk_delete_success, doc_bulk_delete_message = test_document_bulk_delete()
    
    # Test mixed ownership
    mixed_ownership_success, mixed_ownership_message = test_mixed_ownership()
    
    # Test invalid token
    invalid_token_success, invalid_token_message = test_invalid_token()
    
    # Print summary of all tests
    print_summary()
    
    # Print final conclusion
    print("\n" + "="*80)
    print("BULK DELETE API ENDPOINTS ASSESSMENT")
    print("="*80)
    
    all_tests_passed = conv_bulk_delete_success and doc_bulk_delete_success and mixed_ownership_success and invalid_token_success
    
    if all_tests_passed:
        print("✅ All bulk delete API endpoints are working correctly!")
        print("✅ DELETE /api/conversation-history/bulk correctly deletes multiple conversations")
        print("✅ DELETE /api/documents/bulk correctly deletes multiple documents")
        print("✅ Both endpoints properly enforce authentication and ownership")
        print("✅ Both endpoints handle edge cases correctly (empty arrays, non-existent IDs)")
    else:
        print("❌ Some bulk delete API endpoints have issues:")
        if not conv_bulk_delete_success:
            print(f"  - {conv_bulk_delete_message}")
        if not doc_bulk_delete_success:
            print(f"  - {doc_bulk_delete_message}")
        if not mixed_ownership_success:
            print(f"  - {mixed_ownership_message}")
        if not invalid_token_success:
            print(f"  - {invalid_token_message}")
    print("="*80)
    
    return all_tests_passed

if __name__ == "__main__":
    main()
