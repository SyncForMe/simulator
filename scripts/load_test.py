#!/usr/bin/env python3
"""
Load testing script for Observer AI platform
Tests concurrent user registration, authentication, and API usage
"""

import asyncio
import aiohttp
import time
import random
import json
from concurrent.futures import ThreadPoolExecutor
import argparse

class LoadTester:
    def __init__(self, base_url="http://localhost:8001", max_concurrent=100):
        self.base_url = base_url
        self.max_concurrent = max_concurrent
        self.results = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0,
            "max_response_time": 0,
            "min_response_time": float('inf'),
            "errors": []
        }
        
    async def register_user(self, session, user_id):
        """Register a new user"""
        user_data = {
            "email": f"test.user.{user_id}@loadtest.com",
            "password": "TestPassword123",
            "name": f"Test User {user_id}"
        }
        
        start_time = time.time()
        try:
            async with session.post(f"{self.base_url}/api/auth/register", json=user_data) as response:
                duration = time.time() - start_time
                self.update_stats(duration, response.status == 200)
                
                if response.status == 200:
                    data = await response.json()
                    return data.get("access_token")
                else:
                    error_text = await response.text()
                    self.results["errors"].append(f"Registration failed: {error_text}")
                    return None
                    
        except Exception as e:
            duration = time.time() - start_time
            self.update_stats(duration, False)
            self.results["errors"].append(f"Registration error: {str(e)}")
            return None
    
    async def test_api_endpoints(self, session, token, user_id):
        """Test various API endpoints with authentication"""
        headers = {"Authorization": f"Bearer {token}"}
        
        endpoints = [
            ("GET", "/api/agents"),
            ("GET", "/api/conversations"),
            ("GET", "/api/documents"),
            ("GET", "/api/saved-agents"),
        ]
        
        for method, endpoint in endpoints:
            start_time = time.time()
            try:
                async with session.request(method, f"{self.base_url}{endpoint}", headers=headers) as response:
                    duration = time.time() - start_time
                    self.update_stats(duration, response.status == 200)
                    
                    if response.status != 200:
                        error_text = await response.text()
                        self.results["errors"].append(f"{method} {endpoint} failed: {error_text}")
                        
            except Exception as e:
                duration = time.time() - start_time
                self.update_stats(duration, False)
                self.results["errors"].append(f"{method} {endpoint} error: {str(e)}")
    
    async def create_agent(self, session, token, user_id):
        """Create a new agent"""
        agent_data = {
            "name": f"Test Agent {user_id}",
            "archetype": "researcher",
            "goal": "Test goal for load testing",
            "expertise": "Load testing",
            "background": "AI agent created for load testing purposes",
            "personality": {
                "extroversion": 5,
                "optimism": 7,
                "curiosity": 8,
                "cooperativeness": 6,
                "energy": 5
            }
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        start_time = time.time()
        
        try:
            async with session.post(f"{self.base_url}/api/agents", json=agent_data, headers=headers) as response:
                duration = time.time() - start_time
                self.update_stats(duration, response.status == 200)
                
                if response.status != 200:
                    error_text = await response.text()
                    self.results["errors"].append(f"Agent creation failed: {error_text}")
                    
        except Exception as e:
            duration = time.time() - start_time
            self.update_stats(duration, False)
            self.results["errors"].append(f"Agent creation error: {str(e)}")
    
    async def simulate_user_session(self, session, user_id):
        """Simulate a complete user session"""
        print(f"Starting user session {user_id}")
        
        # Register user
        token = await self.register_user(session, user_id)
        if not token:
            return
        
        # Test API endpoints
        await self.test_api_endpoints(session, token, user_id)
        
        # Create an agent
        await self.create_agent(session, token, user_id)
        
        # Random delay to simulate realistic usage
        await asyncio.sleep(random.uniform(0.1, 1.0))
        
        print(f"Completed user session {user_id}")
    
    def update_stats(self, duration, success):
        """Update performance statistics"""
        self.results["total_requests"] += 1
        if success:
            self.results["successful_requests"] += 1
        else:
            self.results["failed_requests"] += 1
        
        self.results["max_response_time"] = max(self.results["max_response_time"], duration)
        self.results["min_response_time"] = min(self.results["min_response_time"], duration)
        
        # Calculate running average
        total = self.results["total_requests"]
        current_avg = self.results["avg_response_time"]
        self.results["avg_response_time"] = (current_avg * (total - 1) + duration) / total
    
    async def run_load_test(self, num_users, concurrent_limit=None):
        """Run load test with specified number of users"""
        if concurrent_limit is None:
            concurrent_limit = min(self.max_concurrent, num_users)
        
        print(f"Starting load test with {num_users} users, {concurrent_limit} concurrent sessions")
        
        connector = aiohttp.TCPConnector(limit=concurrent_limit * 2)
        timeout = aiohttp.ClientTimeout(total=60)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(concurrent_limit)
            
            async def limited_session(user_id):
                async with semaphore:
                    await self.simulate_user_session(session, user_id)
            
            # Run all user sessions
            start_time = time.time()
            tasks = [limited_session(i) for i in range(num_users)]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            total_duration = time.time() - start_time
            
        # Print results
        self.print_results(total_duration, num_users)
    
    def print_results(self, total_duration, num_users):
        """Print load test results"""
        print("\n" + "="*80)
        print("LOAD TEST RESULTS")
        print("="*80)
        print(f"Total Users: {num_users}")
        print(f"Total Duration: {total_duration:.2f} seconds")
        print(f"Total Requests: {self.results['total_requests']}")
        print(f"Successful Requests: {self.results['successful_requests']}")
        print(f"Failed Requests: {self.results['failed_requests']}")
        print(f"Success Rate: {(self.results['successful_requests']/max(self.results['total_requests'],1)*100):.2f}%")
        print(f"Average Response Time: {self.results['avg_response_time']:.3f} seconds")
        print(f"Min Response Time: {self.results['min_response_time']:.3f} seconds")
        print(f"Max Response Time: {self.results['max_response_time']:.3f} seconds")
        print(f"Requests per Second: {self.results['total_requests']/total_duration:.2f}")
        print(f"Users per Second: {num_users/total_duration:.2f}")
        
        if self.results['errors']:
            print(f"\nErrors ({len(self.results['errors'])}):")
            for error in self.results['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.results['errors']) > 10:
                print(f"  ... and {len(self.results['errors']) - 10} more errors")

async def main():
    parser = argparse.ArgumentParser(description="Load test Observer AI platform")
    parser.add_argument("--users", type=int, default=100, help="Number of users to simulate")
    parser.add_argument("--concurrent", type=int, default=50, help="Maximum concurrent sessions")
    parser.add_argument("--url", default="http://localhost:8001", help="Base URL for the API")
    
    args = parser.parse_args()
    
    tester = LoadTester(base_url=args.url, max_concurrent=args.concurrent)
    await tester.run_load_test(args.users, args.concurrent)

if __name__ == "__main__":
    asyncio.run(main())