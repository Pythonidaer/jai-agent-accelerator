#!/usr/bin/env python3
"""
Test script for rate limiting.

Usage:
    # Test locally (make sure server is running)
    python3 test_rate_limiting.py local

    # Test production
    python3 test_rate_limiting.py production https://your-app.vercel.app
"""

import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

def make_request(base_url: str, endpoint: str, count: int = 15) -> List[Tuple[int, int]]:
    """Make multiple requests and return (status_code, request_number) tuples."""
    results = []
    url = f"{base_url}/{endpoint.lstrip('/')}"
    
    def make_single_request(num: int) -> Tuple[int, int]:
        try:
            if endpoint.startswith("/chat") or endpoint.startswith("/api/chat"):
                response = requests.post(
                    url,
                    json={"message": f"test request {num}"},
                    timeout=10
                )
            else:
                response = requests.get(url, timeout=10)
            return (response.status_code, num)
        except Exception as e:
            print(f"  Request {num} failed: {e}")
            return (0, num)
    
    print(f"\nMaking {count} requests to {url}...")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_single_request, i+1) for i in range(count)]
        for future in as_completed(futures):
            status, num = future.result()
            results.append((status, num))
            if status == 429:
                print(f"  ✅ Request {num}: Rate limited (429) - Rate limiting is working!")
            elif status == 200:
                print(f"  ✓ Request {num}: Success (200)")
            else:
                print(f"  ⚠️  Request {num}: Status {status}")
    
    return results

def analyze_results(results: List[Tuple[int, int]], limit: int):
    """Analyze rate limiting results."""
    status_codes = [status for status, _ in results]
    success_count = status_codes.count(200)
    rate_limited_count = status_codes.count(429)
    other_count = len(status_codes) - success_count - rate_limited_count
    
    print(f"\n{'='*60}")
    print(f"Rate Limiting Test Results")
    print(f"{'='*60}")
    print(f"Total Requests: {len(results)}")
    print(f"Successful (200): {success_count}")
    print(f"Rate Limited (429): {rate_limited_count}")
    print(f"Other Status Codes: {other_count}")
    print(f"Expected Limit: {limit} requests/minute")
    
    if rate_limited_count > 0:
        print(f"\n✅ Rate limiting is WORKING!")
        print(f"   {rate_limited_count} requests were rate limited (429 status)")
        if success_count <= limit:
            print(f"   ✅ {success_count} requests succeeded (within limit)")
        else:
            print(f"   ⚠️  {success_count} requests succeeded (more than limit - may need adjustment)")
    else:
        print(f"\n⚠️  Rate limiting may NOT be working")
        print(f"   No 429 responses received")
        print(f"   All {success_count} requests succeeded")
        if success_count > limit:
            print(f"   ⚠️  {success_count} requests succeeded, but limit is {limit}/minute")
            print(f"   Note: Rate limits are per-minute, so rapid requests may all succeed")
            print(f"   Try waiting 60 seconds and running the test again")

def test_local():
    """Test rate limiting on local server."""
    base_url = "http://localhost:8123"  # Local server doesn't use /api prefix
    
    print("="*60)
    print("Testing Rate Limiting - LOCAL")
    print("="*60)
    print("\n⚠️  Make sure your local server is running:")
    print("   cd apps/agent")
    print("   python -m uvicorn pmm_agent.server:app --host 0.0.0.0 --port 8123")
    
    input("\nPress Enter when server is running...")
    
    # Test health endpoint (limit: 60/minute)
    print("\n" + "="*60)
    print("Test 1: Health Endpoint (limit: 60/minute)")
    print("="*60)
    results = make_request(base_url, "/health", count=70)
    analyze_results(results, limit=60)
    
    # Test chat endpoint (limit: 10/minute)
    print("\n" + "="*60)
    print("Test 2: Chat Endpoint (limit: 10/minute)")
    print("="*60)
    results = make_request(base_url, "/chat", count=15)
    analyze_results(results, limit=10)
    
    print("\n" + "="*60)
    print("Local Testing Complete!")
    print("="*60)

def test_production(base_url: str):
    """Test rate limiting on production server."""
    # Remove trailing slash
    base_url = base_url.rstrip("/")
    # Ensure it includes /api if not already there
    if not base_url.endswith("/api"):
        base_url = f"{base_url}/api"
    
    print("="*60)
    print(f"Testing Rate Limiting - PRODUCTION")
    print(f"URL: {base_url}")
    print("="*60)
    
    # Test health endpoint (limit: 60/minute)
    print("\n" + "="*60)
    print("Test 1: Health Endpoint (limit: 60/minute)")
    print("="*60)
    results = make_request(base_url, "/health", count=70)
    analyze_results(results, limit=60)
    
    # Test chat endpoint (limit: 10/minute)
    print("\n" + "="*60)
    print("Test 2: Chat Endpoint (limit: 10/minute)")
    print("="*60)
    print("Note: Chat requests are more expensive, so we'll test with fewer requests")
    results = make_request(base_url, "/chat", count=15)
    analyze_results(results, limit=10)
    
    print("\n" + "="*60)
    print("Production Testing Complete!")
    print("="*60)
    print("\n💡 Tip: Rate limits are per IP address per minute.")
    print("   If all requests succeed, wait 60 seconds and try again.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "local":
        test_local()
    elif mode == "production":
        if len(sys.argv) < 3:
            print("Error: Production URL required")
            print("Usage: python3 test_rate_limiting.py production https://your-app.vercel.app")
            sys.exit(1)
        test_production(sys.argv[2])
    else:
        print(f"Error: Unknown mode '{mode}'")
        print("Usage: python3 test_rate_limiting.py [local|production] [url]")
        sys.exit(1)

