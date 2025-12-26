# Debugging Guide for Exercise 2

This guide helps you identify and fix issues with the Clarification Protocol in Exercise 2.

## Quick Start

### 1. Run the Test Suite

```bash
cd apps/agent
source .venv/bin/activate
export ANTHROPIC_API_KEY=sk-ant-your-key-here
python tests/run_exercise2_test.py
```

This will:
- Run 5 test iterations
- Check if the agent follows the clarification protocol
- Identify specific issues
- Export detailed results to `logs/exercise2_test_results.json`

### 2. Check Live Logs

While the server is running, logs are written to:
- **Console**: Real-time logging with protocol status
- **File**: `apps/agent/logs/agent.log` (detailed debug logs)
- **Events**: `apps/agent/logs/events_YYYYMMDD.jsonl` (structured event data)

### 3. View Metrics via API

```bash
# Get all session metrics
curl http://localhost:8123/metrics

# Get specific session metrics
curl http://localhost:8123/metrics/session/{session_id}

# Export all metrics
curl -X POST http://localhost:8123/metrics/export
```

## Understanding the Output

### Test Results

The test suite checks:
- ✅ **PASS**: Agent asked a question AND did NOT call tools
- ❌ **FAIL**: Agent called tools before asking a question (or didn't ask at all)

### Common Issues

#### Issue 1: "Agent called X tools without asking a question first"
**Cause**: The agent is ignoring the Clarification Protocol instruction
**Fix**: 
- Move the Clarification Protocol section earlier in the prompt (before "Your Workflow")
- Make the instruction more explicit with bold text and "CRITICAL" warnings
- Check if conflicting instructions exist (e.g., "Use `analyze_product` immediately")

#### Issue 2: "Agent asked a question but also called X tools immediately"
**Cause**: The agent is asking AND calling tools in the same response
**Fix**:
- Make the protocol more explicit: "STOP IMMEDIATELY - Do NOT call any tools"
- Add: "Your clarifying question response must contain ONLY the question, nothing else"

#### Issue 3: Inconsistent behavior (sometimes works, sometimes doesn't)
**Cause**: Non-deterministic LLM behavior or prompt ambiguity
**Fix**:
- Review the logs to see what's different between successful and failed attempts
- Check if certain user messages trigger different behavior
- Consider making the protocol even more explicit

## Analyzing Logs

### View Protocol Violations

```bash
# Count violations
grep "PROTOCOL VIOLATION" apps/agent/logs/agent.log

# See which tools were called
grep "TOOL" apps/agent/logs/agent.log | grep -v "TOOL ERROR"
```

### Check Event Data

```bash
# View recent events
tail -n 20 apps/agent/logs/events_*.jsonl | jq '.followed_clarification_protocol'
```

## Debugging Workflow

1. **Run the test suite** to get baseline metrics
2. **Check the logs** to see what's happening
3. **Identify the pattern**: 
   - Is it always the same tool being called?
   - Is it happening on first message only?
   - Is it specific user messages?
4. **Modify the prompt** based on findings
5. **Re-test** to verify the fix
6. **Compare metrics** before/after

## Observability Features

### What Gets Tracked

- **Tool Calls**: Which tools, when, with what arguments
- **Response Times**: How long each response takes
- **Protocol Compliance**: Whether clarification protocol was followed
- **Session Metrics**: Aggregated stats per conversation

### Log Levels

- **INFO**: Normal operations, tool calls, responses
- **WARNING**: Protocol violations, unexpected behavior
- **ERROR**: Tool failures, exceptions

## Next Steps

Once you identify the issue:

1. **If it's a prompt issue**: Modify `prompts.py` and restart server
2. **If it's a tool issue**: Check the tool implementation in `tools/`
3. **If it's routing**: Check if subagents are being used (currently they're not in `server.py`)

## Example Debugging Session

```bash
# 1. Start server with logging
cd apps/agent
source .venv/bin/activate
export ANTHROPIC_API_KEY=sk-ant-your-key-here
python -m uvicorn pmm_agent.server:app --host 0.0.0.0 --port 8123

# 2. In another terminal, run tests
python tests/run_exercise2_test.py

# 3. Check results
cat logs/exercise2_test_results.json | jq '.results[0]'

# 4. View live logs
tail -f logs/agent.log | grep -E "(PROTOCOL|TOOL)"
```

## Metrics Endpoints

- `GET /metrics` - All session metrics
- `GET /metrics/session/{session_id}` - Specific session
- `POST /metrics/export` - Export to JSON file

