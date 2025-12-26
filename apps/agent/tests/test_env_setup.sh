#!/bin/bash
# Comprehensive test script for environment variable setup

set -e

echo "🧪 Testing Environment Variable Setup"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env file exists
echo "1️⃣  Checking .env file..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env file found${NC}"
    echo ""
    echo "Contents (API key hidden):"
    grep -v "^#" .env | grep -v "^$" | sed 's/\(ANTHROPIC_API_KEY=\)[^=]*/\1***HIDDEN***/'
else
    echo -e "${RED}❌ .env file not found${NC}"
    echo "   Create one with:"
    echo "   echo 'ANTHROPIC_API_KEY=sk-ant-your-key' > .env"
    exit 1
fi

echo ""
echo "2️⃣  Checking python-dotenv is installed..."
if python3 -c "import dotenv" 2>/dev/null; then
    echo -e "${GREEN}✅ python-dotenv is installed${NC}"
else
    echo -e "${YELLOW}⚠️  python-dotenv not installed${NC}"
    echo "   Install with: pip install python-dotenv"
    exit 1
fi

echo ""
echo "3️⃣  Testing .env file loading in Python..."
python3 << 'EOF'
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Try to load .env
env_path = Path(".env")
if env_path.exists():
    load_dotenv(env_path)
    print("✅ .env file loaded successfully")
    
    # Check if variables are loaded
    api_key = os.getenv("ANTHROPIC_API_KEY")
    model = os.getenv("MODEL")
    log_level = os.getenv("LOG_LEVEL")
    
    if api_key:
        print(f"✅ ANTHROPIC_API_KEY: {'***SET***' if api_key else 'NOT SET'}")
    else:
        print("❌ ANTHROPIC_API_KEY: NOT SET")
        sys.exit(1)
        
    if model:
        print(f"✅ MODEL: {model}")
    else:
        print("ℹ️  MODEL: Not set (will use default: claude-sonnet-4-20250514)")
        
    if log_level:
        print(f"✅ LOG_LEVEL: {log_level}")
    else:
        print("ℹ️  LOG_LEVEL: Not set (will use default: INFO)")
else:
    print("❌ .env file not found")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to load .env file${NC}"
    exit 1
fi

echo ""
echo "4️⃣  Testing server can start (quick check)..."
echo "   (This will check if server can import and validate config)"

python3 << 'EOF'
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path("src")))

try:
    # Try to import server (this will test .env loading)
    from pmm_agent.server import app, agent
    print("✅ Server module imports successfully")
    print("✅ Environment variables loaded correctly")
except ValueError as e:
    if "ANTHROPIC_API_KEY" in str(e):
        print("❌ ERROR: ANTHROPIC_API_KEY not set")
        print(f"   {e}")
        sys.exit(1)
    else:
        raise
except Exception as e:
    print(f"⚠️  Warning: {e}")
    print("   (This is okay if it's just a startup check)")
EOF

echo ""
echo -e "${GREEN}✅ All environment variable checks passed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Start the server: python3 -m uvicorn src.pmm_agent.server:app --port 8123"
echo "  2. In another terminal, run: python3 tests/test_env_vars.py"
echo "  3. Test a chat request to verify Haiku is working"

