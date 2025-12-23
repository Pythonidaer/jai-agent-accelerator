# Observability & Testing Setup for Exercise 2

## What Was Added

### 1. Observability Module (`src/pmm_agent/observability.py`)

A comprehensive logging and metrics system that tracks:
- **Tool Calls**: Which tools are called, when, with what arguments
- **Agent Responses**: Full response text, timing, protocol compliance
- **Session Metrics**: Aggregated stats per conversation
- **Protocol Violations**: Automatic detection of when clarification protocol is violated

**Features:**
- Console logging (INFO level)
- File logging (DEBUG level) to `logs/agent.log`
- Structured event logging to `logs/events_YYYYMMDD.jsonl`
- Metrics export to JSON

### 2. Test Suite (`src/pmm_agent/test_exercise2.py`)

Automated testing framework that:
- Tests clarification protocol behavior
- Runs multiple iterations to check consistency
- Identifies specific issues (which tools called, why protocol failed)
- Exports detailed results

### 3. Server Integration (`server.py`)

Enhanced the streaming endpoint to:
- Track all tool calls with timestamps
- Log responses with protocol analysis
- Provide metrics endpoints

### 4. Test Runner (`run_exercise2_test.py`)

Simple script to run tests:
```bash
python run_exercise2_test.py
```

### 5. Debugging Guide (`DEBUGGING_GUIDE.md`)

Complete guide on how to use the observability tools.

## How to Use

### Step 1: Run Tests

```bash
cd apps/agent
source .venv/bin/activate
export ANTHROPIC_API_KEY=sk-ant-your-key-here
python run_exercise2_test.py
```

This will:
- Run 5 test iterations
- Show pass/fail for each
- Identify specific issues
- Export results to `logs/exercise2_test_results.json`

### Step 2: Check Logs

While your server is running, logs are automatically written:

```bash
# View live logs
tail -f logs/agent.log

# Check for protocol violations
grep "PROTOCOL VIOLATION" logs/agent.log

# See tool calls
grep "TOOL" logs/agent.log
```

### Step 3: View Metrics

```bash
# Get all metrics
curl http://localhost:8123/metrics

# Get specific session
curl http://localhost:8123/metrics/session/{session_id}

# Export all metrics
curl -X POST http://localhost:8123/metrics/export
```

## What You'll See

### Console Output (when server is running)

```
[INFO] [TOOL] analyze_product | Session: abc12345... | Args: {...}
[INFO] [RESPONSE] Session: abc12345... | Protocol: ❌ VIOLATED | Tools: 2 | Time: 1234ms
[WARNING] [PROTOCOL VIOLATION] Agent called 2 tools before asking clarifying question. Tools: ['analyze_product', 'extract_value_props']
```

### Test Output

```
================================================================================
EXERCISE 2: PROMPT SURGERY - TEST SUITE
================================================================================

Testing Clarification Protocol behavior...

[TEST] Testing clarification protocol with: 'Help me position my SaaS product'
[TOOL] analyze_product | Session: test_session_0... | Args: {...}
[TEST RESULT] Protocol: ❌ FAILED
[TEST ISSUE] Agent called 1 tools without asking a question first. Tools: ['analyze_product']

================================================================================
TEST RESULTS SUMMARY
================================================================================
Total Tests: 5
Passed: 1 ✅
Failed: 4 ❌
Pass Rate: 20.0%

Issues Found:
  [4x] Agent called 1 tools without asking a question first. Tools: ['analyze_product']
  [1x] None - Protocol followed correctly
```

## Understanding the Results

### Protocol Analysis

The system automatically detects:
- ✅ **Followed**: Asked question, no tools called
- ❌ **Violated**: Called tools before asking (or didn't ask at all)
- ⚠️ **Partial**: Asked question but also called tools immediately

### Issue Identification

The test suite identifies specific problems:
1. **"Agent called X tools without asking a question first"**
   - The agent is ignoring the clarification protocol
   - Likely a prompt issue - instruction not strong enough or too late in prompt

2. **"Agent asked a question but also called X tools immediately"**
   - The agent is trying to do both
   - Need to make protocol more explicit: "STOP - do NOT call tools"

3. **Inconsistent results**
   - Non-deterministic behavior
   - Check logs to see what's different between runs

## Next Steps for Debugging

1. **Run the test suite** to get baseline
2. **Check which tools are being called** - is it always the same tool?
3. **Review the prompt** - is the Clarification Protocol instruction:
   - Early enough in the prompt?
   - Explicit enough?
   - Conflicting with other instructions?
4. **Modify and re-test** - iterate until pass rate improves

## Files Created

- `src/pmm_agent/observability.py` - Logging and metrics
- `src/pmm_agent/test_exercise2.py` - Test framework
- `run_exercise2_test.py` - Test runner script
- `DEBUGGING_GUIDE.md` - Complete debugging guide
- `OBSERVABILITY_SETUP.md` - This file

## Log Files Generated

- `logs/agent.log` - Detailed debug logs
- `logs/events_YYYYMMDD.jsonl` - Structured event data (one JSON per line)
- `logs/exercise2_test_results.json` - Test results
- `logs/metrics_YYYYMMDD_HHMMSS.json` - Exported metrics

## Integration Notes

- Observability is automatically enabled when server starts
- No configuration needed - logs go to `apps/agent/logs/`
- Metrics endpoints are available at `/metrics`
- All logging is non-blocking and won't slow down responses

