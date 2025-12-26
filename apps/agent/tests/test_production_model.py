#!/usr/bin/env python3
"""
Test script to verify which model is being used in production.

Compares response characteristics to identify if Haiku or Sonnet 4 is being used.
"""

import sys
import time
import requests
from datetime import datetime


def test_model_in_production(base_url: str):
    """Test production endpoint to identify which model is being used."""
    print("=" * 60)
    print("Testing Production Model")
    print("=" * 60)
    print(f"📍 URL: {base_url}")
    print(f"⏰ Started: {datetime.now().isoformat()}\n")
    
    # Test 1: Health endpoint (should be fast, cached)
    print("1️⃣  Testing health endpoint (baseline)...")
    start = time.time()
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        health_time = (time.time() - start) * 1000
        if response.status_code == 200:
            print(f"   ✅ Health check: {health_time:.0f}ms (expected: <100ms)")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Simple chat request (tests model speed)
    print("\n2️⃣  Testing simple chat request...")
    test_message = "What are you? Respond in one sentence."
    start = time.time()
    try:
        response = requests.post(
            f"{base_url}/chat",
            json={"message": test_message},
            headers={"Content-Type": "application/json"},
            timeout=30  # Allow up to 30 seconds
        )
        chat_time = (time.time() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get("response", "")
            response_length = len(response_text)
            
            print(f"   ✅ Response received: {chat_time:.0f}ms")
            print(f"   📝 Response length: {response_length} characters")
            print(f"   💬 Preview: {response_text[:100]}...")
            
            # Analyze timing to estimate model
            print(f"\n3️⃣  Analyzing response characteristics...")
            
            # Haiku is typically faster (1-3 seconds)
            # Sonnet 4 is typically slower (3-6 seconds)
            if chat_time < 3000:
                print(f"   ⚡ Response time: {chat_time:.0f}ms (< 3s)")
                print(f"   🎯 Likely model: **Haiku** (fast responses)")
            elif chat_time < 6000:
                print(f"   ⚡ Response time: {chat_time:.0f}ms (3-6s)")
                print(f"   🎯 Likely model: **Sonnet 4** (slower but more capable)")
            else:
                print(f"   ⚡ Response time: {chat_time:.0f}ms (> 6s)")
                print(f"   🎯 Likely model: **Sonnet 4** or network latency")
            
            # Additional indicators
            if "tool" in data and data["tool"]:
                print(f"   🔧 Tool calls detected: {len(data.get('tool_calls', []))}")
            
            return True
        else:
            print(f"   ❌ Chat request failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ⏱️  Request timed out (> 30s)")
        print(f"   🎯 Likely model: **Sonnet 4** (complex processing)")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_streaming_endpoint(base_url: str):
    """Test streaming endpoint to check response speed."""
    print("\n4️⃣  Testing streaming endpoint...")
    test_message = "What are you?"
    start = time.time()
    first_chunk_time = None
    
    try:
        response = requests.post(
            f"{base_url}/chat/stream",
            json={"message": test_message},
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    chunk_count += 1
                    if chunk_count == 1 and first_chunk_time is None:
                        first_chunk_time = (time.time() - start) * 1000
            
            total_time = (time.time() - start) * 1000
            
            print(f"   ✅ Stream received: {total_time:.0f}ms total")
            if first_chunk_time:
                print(f"   ⚡ First chunk: {first_chunk_time:.0f}ms")
                
                # Time to first token (TTFT) is often faster with Haiku
                if first_chunk_time < 1500:
                    print(f"   🎯 Fast TTFT suggests: **Haiku**")
                else:
                    print(f"   🎯 Slower TTFT suggests: **Sonnet 4**")
            
            return True
        else:
            print(f"   ❌ Streaming request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def check_vercel_env():
    """Helper to check Vercel environment variables."""
    print("\n" + "=" * 60)
    print("Vercel Environment Check")
    print("=" * 60)
    print("\nTo check if MODEL is set in Vercel:")
    print("  vercel env ls")
    print("\nNote: If MODEL shows as 'encrypted', it's still set.")
    print("The value is hidden but the variable exists.")
    print("\nTo see the actual value, check Vercel dashboard:")
    print("  https://vercel.com/dashboard -> Your Project -> Settings -> Environment Variables")


def main():
    """Run production model tests."""
    if len(sys.argv) < 2:
        print("Usage: python3 tests/test_production_model.py <production-url>")
        print("\nExample:")
        print("  python3 tests/test_production_model.py https://my-pmm-agent.vercel.app")
        print("\nOr check Vercel logs directly:")
        print("  vercel logs https://my-pmm-agent.vercel.app")
        print("  (Look for '🤖 Agent initialized with model: ...')")
        check_vercel_env()
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    
    # Remove /api if present (we add it back)
    if base_url.endswith('/api'):
        base_url = base_url[:-4]
    
    # Add /api prefix if not present
    if not base_url.endswith('/api'):
        api_url = f"{base_url}/api"
    else:
        api_url = base_url
    
    print(f"\n🔍 Testing Production Model Configuration")
    print(f"📍 Base URL: {base_url}")
    print(f"🔗 API URL: {api_url}\n")
    
    try:
        # Test health first
        health_ok = test_model_in_production(api_url)
        
        if health_ok:
            # Test streaming
            test_streaming_endpoint(api_url)
        
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        print("\n💡 Model Identification Tips:")
        print("   • Haiku: Typically 1-3 seconds, fast responses")
        print("   • Sonnet 4: Typically 3-6 seconds, more detailed responses")
        print("\n📋 To verify exactly which model is set:")
        print("   1. Check env vars: vercel env ls")
        print("      (If MODEL shows as 'encrypted', it's set but value is hidden)")
        print("   2. Check Vercel logs:")
        print("      vercel logs https://your-app.vercel.app")
        print("      (Look for '🤖 Agent initialized with model: ...')")
        print("   3. Check Vercel dashboard:")
        print("      https://vercel.com/dashboard -> Project -> Settings -> Environment Variables")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

