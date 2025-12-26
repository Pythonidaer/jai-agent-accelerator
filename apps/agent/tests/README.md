# Test Suite Documentation

This directory contains all test scripts for the PMM Agent project. Tests are organized to verify functionality, deployment readiness, and production behavior.

---

## Quick Reference

| Test File | Type | Purpose | When to Run |
|-----------|------|---------|-------------|
| `test_custom_tools.py` | Python | Verify custom tools work correctly | Before deployment, after tool changes |
| `test_env_vars.py` | Python | Verify environment variables are loaded | Local development setup |
| `test_env_setup.sh` | Shell | Test .env file loading and server import | Initial setup verification |
| `test_input_validation.sh` | Shell | Verify input validation (length limits) | After input validation changes |
| `test_production_model.py` | Python | Identify which model is used in production | After deploying model changes |
| `test_rate_limiting.py` | Python | Verify rate limiting is working | After rate limiting implementation |
| `test_response_caching.py` | Python | Verify response caching (health, metrics) | After caching implementation |
| `test_tool_execution.py` | Python | Basic tool execution verification | Quick tool functionality check |
| `run_deployment_checklist_test.py` | Python | Run comprehensive deployment checklist tests | Before production deployment |
| `run_exercise2_test.py` | Python | Test Exercise 2 (clarification protocol) | When working on Exercise 2 |

---

## Detailed Test Descriptions

### `test_custom_tools.py`

**Purpose:** Verifies that at least 3 custom tools work correctly before deployment.

**What it tests:**
- `calculate_positioning_readiness` - Scoring tool
- `analyze_product` - Product analysis tool
- `create_positioning_statement` - Positioning statement generator
- `extract_value_props` - Value proposition extractor

**Usage:**
```bash
cd apps/agent
source .venv/bin/activate  # Activate virtual environment
python3 tests/test_custom_tools.py
```

**Output:** 
- Console logs showing tool execution results
- JSON log file in `apps/agent/logs/tool_test_*.json`

**Expected Result:** All tested tools execute successfully and return valid results.

**When to run:**
- Before deploying to production
- After modifying tool implementations
- After adding new tools

---

### `test_env_vars.py`

**Purpose:** Verifies that environment variables (MODEL, LOG_LEVEL) are correctly loaded and applied.

**What it tests:**
- `MODEL` environment variable is read correctly
- `LOG_LEVEL` environment variable is respected
- Server can be imported with correct env vars

**Usage:**
```bash
cd apps/agent
export MODEL=claude-3-5-haiku-20241022
export LOG_LEVEL=DEBUG
python3 tests/test_env_vars.py
```

**Expected Result:** 
- Server reads MODEL env var correctly
- Logging level is set appropriately
- No errors when importing server module

**When to run:**
- After setting up local environment
- When switching models locally
- When troubleshooting environment variable issues

---

### `test_env_setup.sh`

**Purpose:** Comprehensive test script for environment variable setup and .env file loading.

**What it tests:**
- .env file exists and is readable
- python-dotenv is installed
- Server module can be imported
- Environment variables are loaded from .env

**Usage:**
```bash
cd apps/agent
./tests/test_env_setup.sh
```

**Output:** Color-coded pass/fail indicators for each test step.

**Expected Result:** All checks pass, confirming environment is set up correctly.

**When to run:**
- Initial project setup
- After cloning the repository
- When troubleshooting .env file loading

**Dependencies:** 
- Requires `python-dotenv` package
- Requires `.env` file in `apps/agent/` directory

---

### `test_input_validation.sh`

**Purpose:** Verifies that input validation is working correctly (message length limits).

**What it tests:**
1. Empty message → Should return 422 (validation error)
2. Very long message (>50,000 chars) → Should return 422
3. Valid message → Should return 200

**Usage:**
```bash
cd apps/agent
./tests/test_input_validation.sh
```

**Note:** This script tests the production URL by default. To test locally, modify the URL in the script.

**Expected Result:**
- Empty message: HTTP 422 with validation error
- Very long message: HTTP 422 with validation error  
- Valid message: HTTP 200 with successful response

**When to run:**
- After implementing input validation
- When verifying Pydantic validation is working
- Before deploying validation changes

---

### `test_production_model.py`

**Purpose:** Identifies which model (Haiku or Sonnet 4) is being used in production by analyzing response characteristics.

**What it tests:**
- Response time characteristics
- Response quality/verbosity
- Model capabilities (reasoning depth)

**Usage:**
```bash
cd apps/agent
python3 tests/test_production_model.py https://my-pmm-agent.vercel.app
```

**Expected Result:** Analysis indicating whether Haiku or Sonnet 4 is being used.

**When to run:**
- After deploying model changes
- When verifying MODEL env var is applied in production
- When troubleshooting model-related issues

**Note:** This is a heuristic test - for definitive confirmation, check Vercel logs for the initialization message.

---

### `test_rate_limiting.py`

**Purpose:** Verifies that rate limiting is working correctly (using `slowapi`).

**What it tests:**
- Health endpoint: 60 requests/minute limit
- Chat endpoint: 10 requests/minute limit
- Metrics endpoint: 30 requests/minute limit
- 429 status code when limit exceeded

**Usage:**
```bash
# Test locally (server must be running on port 8123)
cd apps/agent
python3 tests/test_rate_limiting.py local

# Test production
python3 tests/test_rate_limiting.py production https://my-pmm-agent.vercel.app
```

**Expected Result:**
- Initial requests succeed (200 status)
- After limit exceeded, requests return 429
- Rate limit resets after the time window

**When to run:**
- After implementing rate limiting
- When verifying `slowapi` is working
- Before deploying rate limiting changes

---

### `test_response_caching.py`

**Purpose:** Verifies that response caching is working correctly for performance optimization.

**What it tests:**
- Health endpoint: Uses `@lru_cache` for static responses
- Metrics endpoint: Uses time-based cache (30-second TTL)
- Cached responses return faster

**Usage:**
```bash
# Test locally
cd apps/agent
python3 tests/test_response_caching.py local

# Test production
python3 tests/test_response_caching.py production https://my-pmm-agent.vercel.app
```

**Expected Result:**
- Health endpoint: Returns same cached timestamp for multiple requests
- Metrics endpoint: Returns cached data within 30-second window, then refreshes

**When to run:**
- After implementing caching
- When verifying cache TTL is correct
- When troubleshooting performance issues

**Note:** Chat endpoints are intentionally NOT cached (LLM responses should be fresh).

---

### `test_tool_execution.py`

**Purpose:** Basic test to verify that tools execute successfully.

**What it tests:**
- `analyze_product` tool executes
- Tool returns valid results
- No exceptions during execution

**Usage:**
```bash
cd apps/agent
source .venv/bin/activate
python3 tests/test_tool_execution.py
```

**Expected Result:** Tool executes successfully and returns formatted output.

**When to run:**
- Quick verification after tool changes
- When debugging tool execution issues
- As a smoke test for tool functionality

---

### `run_deployment_checklist_test.py`

**Purpose:** Comprehensive test runner for deployment checklist items.

**What it tests:**
- API key security
- CORS configuration
- Rate limiting (checks for implementation)
- Input validation
- HTTPS enforcement
- Response caching
- Conversation truncation
- Model selection
- Health checks
- Error tracking (checks for Sentry)
- Usage metrics

**Usage:**
```bash
cd apps/agent
python3 tests/run_deployment_checklist_test.py
```

**Expected Result:** Summary of all deployment checklist items with pass/fail status.

**When to run:**
- Before deploying to production
- When verifying deployment readiness
- When reviewing production checklist items

**Note:** This test checks code-level implementations. Some items (like error tracking setup) require additional configuration.

---

### `run_exercise2_test.py`

**Purpose:** Test runner for Exercise 2 (clarification protocol behavior).

**What it tests:**
- Agent asks clarifying questions before proceeding
- Clarification protocol is followed
- Agent waits for answers before using tools

**Usage:**
```bash
cd apps/agent
source .venv/bin/activate
python3 tests/run_exercise2_test.py
```

**Expected Result:** Test suite showing clarification protocol compliance.

**When to run:**
- When working on Exercise 2
- When modifying clarification protocol
- When verifying agent behavior matches requirements

**Dependencies:** Requires the agent to be running locally or accessible.

---

## Running All Tests

To run all tests in sequence:

```bash
cd apps/agent
source .venv/bin/activate

# Environment setup
./tests/test_env_setup.sh

# Environment variables
python3 tests/test_env_vars.py

# Custom tools
python3 tests/test_custom_tools.py

# Deployment checklist
python3 tests/run_deployment_checklist_test.py
```

**Note:** Some tests require the server to be running locally, while others test production endpoints.

---

## Test Dependencies

**Python Dependencies:**
- All tests require Python 3.11+
- Install dependencies: `pip install -e .` (from `apps/agent/` directory)

**Shell Script Dependencies:**
- Bash shell
- `curl` command
- `python3` in PATH

**Server Requirements:**
- Local tests require server running on `http://localhost:8123`
- Production tests require valid Vercel deployment URL

---

## Test Output Locations

- **Console output:** All tests print results to console
- **JSON logs:** `apps/agent/logs/tool_test_*.json` (from `test_custom_tools.py`)
- **Log files:** `apps/agent/logs/` directory

---

## Troubleshooting

### "ModuleNotFoundError" when running tests
- Activate virtual environment: `source .venv/bin/activate`
- Install dependencies: `pip install -e .`

### "Connection refused" errors
- Ensure server is running: `python3 -m uvicorn src.pmm_agent.server:app --port 8123`
- Check server is on correct port

### Tests fail in production
- Verify environment variables are set in Vercel
- Check deployment is successful
- Review Vercel logs for errors

### Shell script permissions
- Make executable: `chmod +x tests/test_*.sh`
- Run with: `./tests/test_*.sh`

---

## Adding New Tests

When adding new tests:

1. **Place in `tests/` directory**
2. **Follow naming convention:**
   - `test_<feature>.py` for Python tests
   - `test_<feature>.sh` for shell scripts
3. **Add documentation** to this README
4. **Update references** in documentation files if needed

---

## Related Documentation

- **Tool Testing Guide:** `apps/agent/TOOL_TESTING.md`
- **Deployment Checklist:** `docs/DEPLOYMENT_CHECKLIST_VERIFICATION.md`
- **Local Setup:** `apps/agent/LOCAL_SETUP.md`
- **Debugging Guide:** `apps/agent/DEBUGGING_GUIDE.md`

