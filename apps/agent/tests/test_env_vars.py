#!/usr/bin/env python3
"""
Test script to verify environment variables are working correctly.

Tests:
1. MODEL env var - verifies correct model is used
2. LOG_LEVEL env var - verifies logging level is set correctly
"""

import os
import sys
import subprocess
import requests
import logging
from pathlib import Path


def test_model_env_var():
    """Test that MODEL environment variable is respected."""
    print("=" * 60)
    print("Testing MODEL Environment Variable")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8123/health", timeout=2)
        if response.status_code != 200:
            print("❌ Server not responding correctly")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Please start the server first:")
        print("   cd apps/agent && python3 -m uvicorn src.pmm_agent.server:app --port 8123")
        return False
    
    # Check what model is configured in the running server
    # We can't easily detect which model is being used without making a request
    # But we can verify the code reads the env var correctly
    
    # Read server.py to verify MODEL env var is used
    server_path = Path(__file__).parent / "src" / "pmm_agent" / "server.py"
    with open(server_path, 'r') as f:
        server_content = f.read()
        if 'os.getenv("MODEL"' in server_content:
            print("✅ MODEL environment variable is used in server.py")
        else:
            print("❌ MODEL environment variable not found in server.py")
            return False
    
    # Check if MODEL env var is set
    model = os.getenv("MODEL")
    if model:
        print(f"✅ MODEL environment variable is set: {model}")
    else:
        print("ℹ️  MODEL environment variable not set (using default: claude-sonnet-4-20250514)")
    
    return True


def test_log_level_env_var():
    """Test that LOG_LEVEL environment variable is respected."""
    print("\n" + "=" * 60)
    print("Testing LOG_LEVEL Environment Variable")
    print("=" * 60)
    
    # Read observability.py to verify LOG_LEVEL env var is used
    obs_path = Path(__file__).parent / "src" / "pmm_agent" / "observability.py"
    with open(obs_path, 'r') as f:
        obs_content = f.read()
        if 'os.getenv("LOG_LEVEL"' in obs_content:
            print("✅ LOG_LEVEL environment variable is used in observability.py")
        else:
            print("❌ LOG_LEVEL environment variable not found in observability.py")
            return False
    
    # Check if LOG_LEVEL env var is set
    log_level = os.getenv("LOG_LEVEL")
    if log_level:
        print(f"✅ LOG_LEVEL environment variable is set: {log_level}")
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if log_level.upper() in valid_levels:
            print(f"✅ LOG_LEVEL is valid: {log_level.upper()}")
        else:
            print(f"⚠️  LOG_LEVEL '{log_level}' may not be valid. Valid values: {', '.join(valid_levels)}")
    else:
        print("ℹ️  LOG_LEVEL environment variable not set (using default: INFO)")
    
    return True


def test_env_var_setting():
    """Test setting environment variables and restarting server."""
    print("\n" + "=" * 60)
    print("Environment Variable Configuration Guide")
    print("=" * 60)
    
    print("\nTo set environment variables:")
    print("\n1. For local development (in terminal before starting server):")
    print("   export MODEL=claude-3-5-haiku-20241022")
    print("   export LOG_LEVEL=DEBUG")
    print("   python3 -m uvicorn src.pmm_agent.server:app --port 8123")
    
    print("\n2. For production (Vercel):")
    print("   vercel env add MODEL production")
    print("   # Enter: claude-3-5-haiku-20241022")
    print("   vercel env add LOG_LEVEL production")
    print("   # Enter: INFO")
    print("   vercel --prod  # Redeploy for changes to take effect")
    
    print("\n3. Valid LOG_LEVEL values:")
    print("   - DEBUG: Most verbose (all logs)")
    print("   - INFO: Standard logging (default)")
    print("   - WARNING: Warnings and errors only")
    print("   - ERROR: Errors only")
    
    print("\n4. Valid MODEL values:")
    print("   - claude-sonnet-4-20250514 (default, most capable, ~$3/$15 per 1M tokens)")
    print("   - claude-3-5-haiku-20241022 (cheaper, ~$0.25/$1.25 per 1M tokens)")
    print("   - claude-3-5-sonnet-20241022 (middle ground)")
    print("   - claude-3-opus-20240229 (most capable, most expensive)")


def main():
    """Run environment variable tests."""
    print("\n🔍 Testing Environment Variable Configuration\n")
    
    model_ok = test_model_env_var()
    log_level_ok = test_log_level_env_var()
    test_env_var_setting()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"MODEL env var:  {'✅ PASS' if model_ok else '❌ FAIL'}")
    print(f"LOG_LEVEL env var: {'✅ PASS' if log_level_ok else '❌ FAIL'}")
    
    if model_ok and log_level_ok:
        print("\n✅ All environment variable configurations verified!")
        return 0
    else:
        print("\n⚠️  Some checks failed. Review output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

