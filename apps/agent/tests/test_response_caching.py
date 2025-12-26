#!/usr/bin/env python3
"""
Test script for response caching verification.

Tests:
1. Health endpoint caching (lru_cache)
2. Metrics endpoint caching (30-second TTL)
"""

import sys
import time
import requests
from datetime import datetime


def test_health_endpoint_caching(base_url: str):
    """Test that health endpoint returns cached responses."""
    print("=" * 60)
    print("Testing Health Endpoint Caching")
    print("=" * 60)
    
    # Make first request
    print("\n1. Making first request...")
    response1 = requests.get(f"{base_url}/health")
    assert response1.status_code == 200, f"Expected 200, got {response1.status_code}"
    data1 = response1.json()
    cached_at_1 = data1.get("cached_at")
    print(f"   ✅ First response received")
    print(f"   Cached at: {cached_at_1}")
    
    # Wait a moment
    time.sleep(0.5)
    
    # Make second request - should return same cached timestamp
    print("\n2. Making second request (should be cached)...")
    response2 = requests.get(f"{base_url}/health")
    assert response2.status_code == 200, f"Expected 200, got {response2.status_code}"
    data2 = response2.json()
    cached_at_2 = data2.get("cached_at")
    print(f"   ✅ Second response received")
    print(f"   Cached at: {cached_at_2}")
    
    # Verify caching: timestamps should be identical (cached)
    if cached_at_1 == cached_at_2:
        print(f"\n   ✅ CACHING WORKING: Both responses have same timestamp (cached)")
        return True
    else:
        print(f"\n   ❌ CACHING NOT WORKING: Timestamps differ")
        print(f"      First:  {cached_at_1}")
        print(f"      Second: {cached_at_2}")
        return False


def test_metrics_endpoint_caching(base_url: str):
    """Test that metrics endpoint caches for 30 seconds."""
    print("\n" + "=" * 60)
    print("Testing Metrics Endpoint Caching (30-second TTL)")
    print("=" * 60)
    
    # Make first request
    print("\n1. Making first request...")
    response1 = requests.get(f"{base_url}/metrics")
    assert response1.status_code == 200, f"Expected 200, got {response1.status_code}"
    data1 = response1.json()
    cached_at_1 = data1.get("cached_at")
    print(f"   ✅ First response received")
    print(f"   Cached at: {cached_at_1}")
    print(f"   Total sessions: {data1.get('summary', {}).get('total_sessions', 'N/A')}")
    
    # Wait 1 second
    print("\n2. Waiting 1 second, then making second request (should be cached)...")
    time.sleep(1)
    response2 = requests.get(f"{base_url}/metrics")
    assert response2.status_code == 200, f"Expected 200, got {response2.status_code}"
    data2 = response2.json()
    cached_at_2 = data2.get("cached_at")
    print(f"   ✅ Second response received")
    print(f"   Cached at: {cached_at_2}")
    
    # Within 30 seconds, should return cached response
    if cached_at_1 == cached_at_2:
        print(f"\n   ✅ CACHING WORKING: Response cached (same timestamp)")
    else:
        print(f"\n   ⚠️  CACHING NOT WORKING: Different timestamps (cache may have expired or not working)")
        print(f"      First:  {cached_at_1}")
        print(f"      Second: {cached_at_2}")
        return False
    
    # Wait 31 seconds (past TTL) and make third request
    print("\n3. Waiting 31 seconds (past 30s TTL), then making third request (should be fresh)...")
    print("   (This will take ~31 seconds...)")
    time.sleep(31)
    response3 = requests.get(f"{base_url}/metrics")
    assert response3.status_code == 200, f"Expected 200, got {response3.status_code}"
    data3 = response3.json()
    cached_at_3 = data3.get("cached_at")
    print(f"   ✅ Third response received")
    print(f"   Cached at: {cached_at_3}")
    
    # After 30 seconds, should return fresh response
    if cached_at_3 != cached_at_1:
        print(f"\n   ✅ TTL WORKING: Fresh response after cache expiry (different timestamp)")
        return True
    else:
        print(f"\n   ⚠️  TTL NOT WORKING: Same timestamp after 31 seconds (cache should have expired)")
        print(f"      First:  {cached_at_1}")
        print(f"      Third:  {cached_at_3}")
        return False


def main():
    """Run caching tests."""
    if len(sys.argv) < 2:
        print("Usage: python3 tests/test_response_caching.py <local|production> [url]")
        print("  local      - Test against http://localhost:8123")
        print("  production - Test against production URL (must provide URL)")
        print("\nExamples:")
        print("  python3 tests/test_response_caching.py local")
        print("  python3 tests/test_response_caching.py production https://my-pmm-agent.vercel.app")
        sys.exit(1)
    
    mode = sys.argv[1]
    
    if mode == "local":
        base_url = "http://localhost:8123"
    elif mode == "production":
        if len(sys.argv) < 3:
            print("Error: Production mode requires URL")
            print("Usage: python3 tests/test_response_caching.py production <url>")
            sys.exit(1)
        base_url = sys.argv[2].rstrip('/')
    else:
        print(f"Error: Unknown mode '{mode}'. Use 'local' or 'production'")
        sys.exit(1)
    
    print(f"\n🔍 Testing Response Caching")
    print(f"📍 Base URL: {base_url}")
    print(f"⏰ Started at: {datetime.now().isoformat()}\n")
    
    try:
        # Test health endpoint caching
        health_result = test_health_endpoint_caching(base_url)
        
        # Test metrics endpoint caching
        metrics_result = test_metrics_endpoint_caching(base_url)
        
        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"Health endpoint caching:  {'✅ PASS' if health_result else '❌ FAIL'}")
        print(f"Metrics endpoint caching: {'✅ PASS' if metrics_result else '❌ FAIL'}")
        
        if health_result and metrics_result:
            print("\n🎉 All caching tests passed!")
            return 0
        else:
            print("\n⚠️  Some caching tests failed. Review output above.")
            return 1
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error: Could not connect to {base_url}")
        print("   Make sure the server is running (for local: python3 -m uvicorn src.pmm_agent.server:app --port 8123)")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

