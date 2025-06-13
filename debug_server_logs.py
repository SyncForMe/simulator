#!/usr/bin/env python3
import requests
import json
import os
import sys
from dotenv import load_dotenv
import uuid
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv('/app/frontend/.env')
load_dotenv('/app/backend/.env')

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL')
if not BACKEND_URL:
    logging.error("Error: REACT_APP_BACKEND_URL not found in environment variables")
    sys.exit(1)

# Ensure the URL ends with /api
API_URL = f"{BACKEND_URL}/api"
logging.info(f"Using API URL: {API_URL}")

# Global variables
auth_token = None
test_user_id = None

def test_login():
    """Login with test endpoint to get auth token"""
    global auth_token, test_user_id
    
    logging.info("Attempting test login...")
    
    try:
        response = requests.post(f"{API_URL}/auth/test-login")
        response.raise_for_status()
        
        data = response.json()
        auth_token = data.get("access_token")
        user_data = data.get("user", {})
        test_user_id = user_data.get("id")
        
        logging.info(f"Test login successful. User ID: {test_user_id}")
        return True
    except Exception as e:
        logging.error(f"Test login failed: {e}")
        return False

def create_test_document():
    """Create a single test document"""
    if not auth_token:
        if not test_login():
            logging.error("Cannot create test document without authentication")
            return None
    
    document_data = {
        "title": f"Test Document {uuid.uuid4()}",
        "category": "Protocol",
        "description": "This is a test document",
        "content": "# Test Document\n\nThis is a test document.",
        "keywords": ["test"],
        "authors": ["Test User"]
    }
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{API_URL}/documents/create", json=document_data, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        document_id = data.get("document_id")
        
        if document_id:
            logging.info(f"Created document with ID: {document_id}")
            return document_id
        else:
            logging.warning("Failed to get document ID")
            return None
    except Exception as e:
        logging.error(f"Failed to create document: {e}")
        return None

def check_server_logs():
    """Check server logs for errors"""
    logging.info("Checking server logs...")
    
    try:
        # Get the last 100 lines of the backend log
        result = subprocess.run(
            ["tail", "-n", "100", "/var/log/supervisor/backend.log"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            log_lines = result.stdout.strip().split("\n")
            logging.info(f"Found {len(log_lines)} log lines")
            
            # Look for error messages
            error_lines = [line for line in log_lines if "ERROR" in line or "error" in line.lower()]
            if error_lines:
                logging.info(f"Found {len(error_lines)} error lines:")
                for line in error_lines:
                    logging.info(f"  {line}")
            else:
                logging.info("No error lines found in logs")
            
            return log_lines
        else:
            logging.error(f"Failed to get server logs: {result.stderr}")
            return []
    except Exception as e:
        logging.error(f"Error checking server logs: {e}")
        return []

def test_delete_endpoint(document_id):
    """Test DELETE /api/documents/bulk endpoint"""
    if not auth_token:
        if not test_login():
            logging.error("Cannot test delete without authentication")
            return False
    
    logging.info(f"Testing DELETE /api/documents/bulk with document ID: {document_id}")
    
    # Clear server logs before test
    subprocess.run(["sudo", "supervisorctl", "restart", "backend"])
    logging.info("Restarted backend to clear logs")
    
    # Wait for server to restart
    import time
    time.sleep(5)
    
    # Prepare request data
    data = [document_id]
    
    # Print request details
    logging.info(f"Request URL: {API_URL}/documents/bulk")
    logging.info(f"Request Method: DELETE")
    logging.info(f"Request Body: {json.dumps(data)}")
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.delete(f"{API_URL}/documents/bulk", json=data, headers=headers)
        
        logging.info(f"Response Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            logging.info(f"Response: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            logging.warning(f"Response is not JSON: {response.text}")
            response_data = {}
        
        # Check server logs after test
        logging.info("Checking server logs after DELETE request...")
        log_lines = check_server_logs()
        
        # Look for specific error messages related to the DELETE request
        delete_errors = [line for line in log_lines if "/documents/bulk" in line and ("ERROR" in line or "error" in line.lower())]
        if delete_errors:
            logging.info(f"Found {len(delete_errors)} DELETE-related error lines:")
            for line in delete_errors:
                logging.info(f"  {line}")
        
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Error during delete test: {e}")
        return False

def test_post_delete_endpoint(document_id):
    """Test POST /api/documents/bulk-delete endpoint"""
    if not auth_token:
        if not test_login():
            logging.error("Cannot test delete without authentication")
            return False
    
    logging.info(f"Testing POST /api/documents/bulk-delete with document ID: {document_id}")
    
    # Clear server logs before test
    subprocess.run(["sudo", "supervisorctl", "restart", "backend"])
    logging.info("Restarted backend to clear logs")
    
    # Wait for server to restart
    import time
    time.sleep(5)
    
    # Prepare request data
    data = {
        "document_ids": [document_id]
    }
    
    # Print request details
    logging.info(f"Request URL: {API_URL}/documents/bulk-delete")
    logging.info(f"Request Method: POST")
    logging.info(f"Request Body: {json.dumps(data)}")
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{API_URL}/documents/bulk-delete", json=data, headers=headers)
        
        logging.info(f"Response Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            logging.info(f"Response: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            logging.warning(f"Response is not JSON: {response.text}")
            response_data = {}
        
        # Check server logs after test
        logging.info("Checking server logs after POST request...")
        log_lines = check_server_logs()
        
        # Look for specific error messages related to the POST request
        post_errors = [line for line in log_lines if "/documents/bulk-delete" in line and ("ERROR" in line or "error" in line.lower())]
        if post_errors:
            logging.info(f"Found {len(post_errors)} POST-related error lines:")
            for line in post_errors:
                logging.info(f"  {line}")
        
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Error during post test: {e}")
        return False

def main():
    """Main function to debug server logs"""
    logging.info("Starting server logs debug script...")
    
    # Login to get auth token
    if not test_login():
        logging.error("Login failed. Exiting.")
        return
    
    # Test DELETE endpoint
    logging.info("\n=== Testing DELETE endpoint ===")
    document_id = create_test_document()
    if document_id:
        test_delete_endpoint(document_id)
    
    # Test POST endpoint
    logging.info("\n=== Testing POST endpoint ===")
    document_id = create_test_document()
    if document_id:
        test_post_delete_endpoint(document_id)
    
    logging.info("\n=== Testing Complete ===")

if __name__ == "__main__":
    main()
