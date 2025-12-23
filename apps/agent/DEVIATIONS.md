# Setup Deviations from Project Instructions

This document tracks deviations from the standard setup instructions that were required to get the project running, as well as successful exercise implementations.

## Date: 2025-01-XX

---

## Initial Setup Issues

These issues were encountered during the initial project setup and configuration.

### Prerequisites Note

**Anthropic API Key Requirement:**
- To obtain an Anthropic API key from [console.anthropic.com](https://console.anthropic.com), a minimum payment of $5 is required
- This is not mentioned in the standard setup instructions but is necessary to create and use an API key
- The $5 serves as an initial credit that can be used for API calls

### Issue 1: Python Version Upgrade Required

**Problem:** 
- System had Python 3.9.6 installed
- Project requires Python 3.11+

**Solution:**
- Upgraded to Python 3.11 using Homebrew: `brew install python@3.11`
- Used `python3.11` explicitly when creating virtual environment

**Command used:**
```bash
python3.11 -m venv .venv
```

### Issue 2: pyproject.toml Configuration Errors

**Problem:**
- `pyproject.toml` referenced `readme = "README.md"` but the file doesn't exist in `apps/agent/`
- `pyproject.toml` had incorrect package path: `packages = ["src/preprod_agent"]` instead of `packages = ["src/pmm_agent"]`

**Error encountered:**
```
OSError: Readme file does not exist: README.md
```

**Solution:**
1. Removed the `readme = "README.md"` line from `pyproject.toml` (line 5)
2. Fixed the package path from `src/preprod_agent` to `src/pmm_agent` (line 26)

**Changes made to `pyproject.toml`:**
- Removed: `readme = "README.md"`
- Changed: `packages = ["src/preprod_agent"]` → `packages = ["src/pmm_agent"]`

### Issue 3: Missing FastAPI and Uvicorn Dependencies

**Problem:**
- `server.py` imports `fastapi` and uses `uvicorn` to run the server
- These packages were not listed in `pyproject.toml` dependencies
- Error: `No module named uvicorn`

**Error encountered:**
```
/Users/johnnyhammond/Documents/jai-agent-accelerator/apps/agent/.venv/bin/python: No module named uvicorn
```

**Solution:**
- Added `fastapi>=0.100.0` and `uvicorn>=0.23.0` to dependencies in `pyproject.toml`

**Changes made to `pyproject.toml`:**
- Added: `"fastapi>=0.100.0"` to dependencies
- Added: `"uvicorn>=0.23.0"` to dependencies

### Issue 4: Syntax Error in F-String (intake.py)

**Problem:**
- `tools/intake.py` line 174 had an f-string expression containing a backslash (`\n`)
- Python doesn't allow backslashes directly in f-string expression parts
- Error: `SyntaxError: f-string expression part cannot include a backslash`

**Error encountered:**
```
File ".../tools/intake.py", line 189
    """
       ^
SyntaxError: f-string expression part cannot include a backslash
```

**Solution:**
- Fixed the f-string by extracting strings containing backslashes outside the f-string expression
- Defined default strings as variables before the f-string, then referenced them in the expression
- This avoids having backslashes (`\n`) inside the f-string expression part

**Code change:**
```python
# Before (broken):
{excluded_segments if excluded_segments else "- Companies too small to need this\n- Teams without the pain point\n- Orgs with conflicting technology"}

# After (fixed):
default_excluded = "- Companies too small to need this\n- Teams without the pain point\n- Orgs with conflicting technology"
excluded_text = excluded_segments if excluded_segments else default_excluded
# Then in f-string: {excluded_text}
```

**File modified:**
- `apps/agent/src/pmm_agent/tools/intake.py` (lines 149-177)

### Issue 5: LangGraph create_react_agent API Change (Version Compatibility Issue)

**Problem:**
- `agent.py` was using `state_modifier` parameter with `create_react_agent()` from LangGraph
- This parameter was deprecated in LangGraph 0.1.9 and removed in version 0.2.0
- Project's `pyproject.toml` specified `langgraph>=0.2.0`, which allows installation of versions that removed this parameter
- Error: `TypeError: create_react_agent() got unexpected keyword arguments: {'state_modifier': ...}`

**Root Cause Analysis:**
- Original code was written for LangGraph <0.2.0 (which supported `state_modifier`)
- Dependency constraint `langgraph>=0.2.0` allows newer versions that removed the parameter
- This created a version mismatch: code written for old API, but dependency allows new API
- The original code would NOT have worked even when first created, due to this mismatch
- When `pip install -e .` runs, it installs the latest compatible version (1.0.5), which breaks the code

**Error encountered:**
```
TypeError: create_react_agent() got unexpected keyword arguments: {'state_modifier': '\n# Product Marketing Intelligence Agent\n...'}
```

**Solution:**
- Changed to pass system prompt via the `system` parameter of `ChatAnthropic` model instead
- Removed `state_modifier` parameter from all `create_react_agent()` calls
- System prompt is now set when initializing the LLM model
- This approach is the recommended way to pass system prompts in LangGraph >=0.2.0

**Code change:**
```python
# Before (broken):
llm = ChatAnthropic(model_name=model_name, max_tokens=8192)
agent = create_react_agent(
    model=llm,
    tools=tools,
    state_modifier=MAIN_SYSTEM_PROMPT,  # This parameter doesn't exist in >=0.2.0
)

# After (fixed):
llm = ChatAnthropic(
    model_name=model_name,
    max_tokens=8192,
    system=MAIN_SYSTEM_PROMPT,  # Pass system prompt to model
)
agent = create_react_agent(
    model=llm,
    tools=tools,
)
```

**Functional Equivalence:**
- For static system prompts (like `MAIN_SYSTEM_PROMPT`), both approaches result in the same behavior
- The system prompt is sent to Claude with each API call in both cases
- The change updates the code to match the current API without changing functionality
- Note: `server.py` doesn't actually use `agent.py` - it creates its own `ChatAnthropic` instance directly
- The fix was necessary to prevent import errors when the package loads (since `agent.py` is imported in `__init__.py`)

**Files modified:**
- `apps/agent/src/pmm_agent/agent.py` (all agent creation functions: `create_pmm_agent`, `create_competitive_analyst`, `create_messaging_specialist`, `create_launch_coordinator`)

**Version Information:**
- Original code created: December 19, 2025 (commit `b5be838`)
- LangGraph version installed: 1.0.5
- LangGraph version constraint: `>=0.2.0` (in `pyproject.toml`)
- `state_modifier` removed in: LangGraph 0.2.0

### Issue 6: Frontend Port Configuration Mismatch (RESOLVED)

**Problem:**
- README documentation states the frontend runs on `http://localhost:3003`
- Initial `vite.config.ts` configuration was set to port `3000`
- This created a discrepancy between documentation and actual behavior

**Initial Observation:**
- When running `npm run dev`, the frontend was starting on `http://localhost:3000`
- README and setup instructions reference `http://localhost:3003`

**Resolution:**
- Updated all port configurations to match README (port 3003) and Exercise 1 success criteria
- Changed `vite.config.ts` server port from 3000 to 3003
- Updated Docker configuration (Dockerfile, nginx.conf, docker-compose.yml) to use port 3003
- All configurations now consistently use port 3003 as specified in documentation and Exercise 1 requirements

**Rationale:**
- Exercise 1 success criteria requires agent running at `http://localhost:3003`
- This change ensures alignment with both README documentation and exercise requirements

**Files modified:**
- `apps/web/vite.config.ts` (port: 3000 → 3003)
- `apps/web/Dockerfile` (EXPOSE: 3000 → 3003)
- `apps/web/nginx.conf` (listen: 3000 → 3003)
- `docker-compose.yml` (ports: "3000:3000" → "3003:3003")

---

## Exercise Implementations

### Exercise 1: Hello, Agent (Success)

**Status:** ✅ Completed successfully

**Purpose:**
- Exercise 1 (Hello, Agent) requires: "Screenshot the response" as part of completion criteria
- Created directory structure to organize exercise artifacts

**Action Taken:**
- Created `apps/agent/screenshots/exercises/1/` directory
- Saved screenshot of agent response to `agent_response.png`
- This fulfills Exercise 1 requirement: "3. Screenshot the response"

**Reference:**
- Exercise 1 documentation: `docs/EXERCISES.md`
- Success criteria: Agent running at `http://localhost:3003` with structured response about positioning

**Deviations:**
- None - Exercise completed as specified in instructions

---

### Exercise 2: Prompt Surgery (Major Debugging Required)

**Purpose:**
- Exercise 1 (Hello, Agent) requires: "Screenshot the response" as part of completion criteria
- Created directory structure to organize exercise artifacts

**Action Taken:**
- Created `apps/agent/screenshots/exercises/1/` directory
- Saved screenshot of agent response to `agent_response.png`
- This fulfills Exercise 1 requirement: "3. Screenshot the response"

**Reference:**
- Exercise 1 documentation: `docs/EXERCISES.md`
- Success criteria: Agent running at `http://localhost:3003` with structured response about positioning

---

**Status:** ✅ Completed after extensive debugging

**Context:**
- Exercise 2 requires implementing a "Clarification Protocol" where the agent asks a clarifying question before calling tools
- During debugging, multiple issues were discovered with tool execution, message formatting, and response streaming

**Root Causes Identified:**

**Root Causes from Initial Code:**

1. **Tool Call ID Mismatch (Anthropic API Error)**
   - Error: `unexpected tool_use_id found in tool_result blocks`
   - Cause: Tool call IDs extracted from streaming chunks didn't match the IDs in the final AI message
   - Impact: Tool results couldn't be properly associated with tool calls, causing API errors
   - **Source**: Initial streaming implementation attempted to extract tool calls from chunks, but IDs didn't match final message structure

2. **Invalid Message Format (Anthropic API Error)**
   - Error: `Input tag 'input_json_delta' found using 'type' does not match any of the expected tags`
   - Cause: Manually merging streaming chunks included internal LangChain structures that Anthropic doesn't accept
   - Impact: API rejected messages when trying to pass tool results back to the LLM
   - **Source**: Initial code attempted to manually merge streaming chunks, which included internal LangChain delta structures

3. **Empty Tool Arguments**
   - Issue: `analyze_product` tool was being called with empty `product_description` argument
   - Cause: LLM wasn't extracting the product description from conversation context
   - Impact: Tool execution failed or produced incorrect results
   - **Source**: Initial tool docstring didn't explicitly guide LLM to extract arguments from conversation context

4. **Missing Observability**
   - Issue: No visibility into agent behavior, tool calls, or protocol compliance
   - Cause: No logging or tracking infrastructure existed
   - Impact: Difficult to debug issues and understand agent behavior
   - **Source**: Initial codebase had no observability/logging system

**Root Causes from Modifications Made During Debugging:**

5. **Raw Code Output in Responses**
   - Issue: Agent responses contained raw Python list/dict structures instead of formatted text
   - Cause: Follow-up responses after tool execution weren't properly extracting text from content lists
   - Impact: Poor user experience with unreadable responses
   - **Source**: During debugging, the follow-up response handling converted entire content lists to strings instead of extracting text items
   - **Introduced by**: Modification to use `str(follow_up_response.content)` which stringified the entire list structure

**Solutions Implemented:**

1. **Fixed Tool Execution Flow (`server.py`)**
   - Changed from streaming chunks to using `ainvoke()` to get complete, properly formatted AI messages
   - Extract tool calls directly from the AI message (not from streaming chunks) to ensure correct IDs
   - Execute tools and create `ToolMessage` objects with matching `tool_call_id`
   - Use `ainvoke()` for follow-up response after tool execution to get coherent response incorporating tool results
   - Added fallback to extract `product_description` from conversation context if tool called with empty args
   - **Reference**: [`ainvoke()` documentation](https://python.langchain.com/v0.1/docs/expression_language/interface/) - LangChain's asynchronous invoke method for Runnable interfaces

2. **Fixed Message Format Issues**
   - Replaced manual chunk merging with `ainvoke()` calls to get properly formatted messages
   - Properly extract text content from both string and list content formats
   - Stream text character-by-character to frontend for real-time UX while maintaining proper message structure

3. **Improved Tool Argument Extraction**
   - Updated `analyze_product` tool docstring to explicitly guide LLM to extract `product_description` from conversation
   - Added fallback logic in `server.py` to extract from most recent user message if tool called with empty args
   - This ensures tools work even if LLM doesn't perfectly extract arguments

4. **Fixed Response Text Extraction**
   - Properly handle both string and list content formats when extracting text
   - Extract text from content lists by filtering for `type == 'text'` items
   - Apply same extraction logic to both initial and follow-up responses

5. **Added Observability Infrastructure**
   - Created `observability.py` with comprehensive logging system
   - Tracks tool calls, agent responses, protocol compliance, and session metrics
   - Logs to both console and files for debugging
   - Detects clarification protocol violations (only on first message)
   - Exports metrics to JSON for analysis

**Key Code Changes in `server.py`:**

```python
# Before: Manual chunk merging (caused format errors)
async for chunk in llm_with_tools.astream(...):
    # Merge chunks manually - includes invalid structures
    # Problem: Tool call IDs from chunks don't match final message
    # Problem: Internal LangChain structures (input_json_delta) included

# After: Use ainvoke for complete messages
ai_message = await llm_with_tools.ainvoke(...)
# Extract tool calls from complete message (correct IDs guaranteed)
# Execute tools with correct IDs
# Get follow-up response with tool results
# Reference: https://python.langchain.com/v0.1/docs/expression_language/interface/
```

**Why `ainvoke()` Instead of `astream()`:**
- `ainvoke()` returns a complete, properly formatted `AIMessage` object
- Tool calls in the message have consistent IDs that match Anthropic's API expectations
- No internal LangChain structures are included in the message
- Message format is guaranteed to be compatible with Anthropic's API
- We still stream the text content character-by-character to the frontend for UX

**Files Modified:**
- `apps/agent/src/pmm_agent/server.py` (major refactoring of streaming and tool execution logic)
- `apps/agent/src/pmm_agent/tools/intake.py` (updated docstring for better LLM guidance)
- `apps/agent/src/pmm_agent/prompts.py` (added Clarification Protocol and bonus question requirement)
- `apps/agent/src/pmm_agent/observability.py` (new file - comprehensive logging system)

**New Files Created:**
- `apps/agent/src/pmm_agent/observability.py` - Observability and logging infrastructure
- `apps/agent/src/pmm_agent/test_exercise2.py` - Automated testing for Exercise 2 protocol
- `apps/agent/run_exercise2_test.py` - Test runner script

**Protocol Violation Detection:**
- The observability system correctly detects protocol violations only on the first message
- Warnings on subsequent messages (after user answers) are expected and not actual violations
- The protocol requires: ask question first → wait for answer → then proceed with tools

**Complete Workflow (How It Works Now):**

The fixed implementation follows this clear workflow:

1. **Initial Request**: User sends first message (e.g., "Help me position my SaaS product")
   - Agent uses `ainvoke()` to get complete response
   - Agent asks clarifying question (no tools called)
   - Text is streamed character-by-character to frontend for real-time UX
   - Protocol violation detection applies here (should be no tools on first message)

2. **User Response**: User answers the clarifying question (e.g., provides product description)
   - Agent receives product description in conversation context
   - Agent now proceeds with analysis using tools

3. **Tool Execution Phase**:
   - Agent uses `ainvoke()` to get complete AI message (may include tool calls)
   - Tool calls are extracted directly from the AI message (ensures correct IDs)
   - Tools are executed with proper arguments (with fallback if args empty)
   - `ToolMessage` objects are created with matching `tool_call_id` from AI message
   - Tool results are added to conversation history

4. **Follow-Up Response**:
   - Agent uses `ainvoke()` again with conversation history (including tool results)
   - LLM generates coherent response that incorporates tool output
   - Text content is properly extracted from response (handles both string and list formats)
   - Text is streamed character-by-character to frontend

5. **Final Response**:
   - Agent streams complete response to frontend
   - Response includes analysis from tools and ends with "What would you like to explore next?"
   - Protocol violation warnings on subsequent messages are expected (protocol only applies to first message)

**Key Insight**: Using `ainvoke()` for complete messages ensures proper message formatting and correct tool call IDs, while still providing streaming UX by manually streaming the text content character-by-character.

**Testing:**
- Created automated test suite to verify clarification protocol compliance
- Observability logs provide detailed debugging information
- Protocol violations are tracked and logged for analysis

---

### Exercise 3: Build Your First Tool (Success)

**Status:** ✅ Completed successfully

**Purpose:**
- Exercise 3 requires creating a custom tool that calculates a "positioning readiness score"
- Goal: Extend the agent with domain-specific functionality

**Implementation Steps:**

1. **Created New Tool File:**
   - Created `apps/agent/src/pmm_agent/tools/scoring.py`
   - Implemented `calculate_positioning_readiness` tool with Pydantic model return type
   - Tool takes 5 boolean parameters to assess positioning readiness
   - Returns structured `ReadinessScore` with score (1-10), strengths, gaps, and next action

2. **Registered Tool:**
   - Added import in `apps/agent/src/pmm_agent/tools/__init__.py`
   - Created `SCORING_TOOLS` list with the new tool
   - Added `SCORING_TOOLS` to `ALL_TOOLS` list
   - Tool automatically available via `server.py` which uses `ALL_TOOLS`

3. **Tool Details:**
   - **Tool Name:** `calculate_positioning_readiness`
   - **Parameters:**
     - `has_target_customer: bool`
     - `has_competitive_alternative: bool`
     - `has_key_differentiator: bool`
     - `has_customer_proof: bool`
     - `has_clear_category: bool`
   - **Return Type:** `ReadinessScore` (Pydantic model)
   - **Scoring Logic:** Each true parameter = 2 points (0-10 scale)

4. **Verification:**
   - Confirmed tool appears in `ALL_TOOLS` (16 tools total)
   - Tool is properly registered and available to the agent
   - No import errors or syntax issues

**Files Created:**
- `apps/agent/src/pmm_agent/tools/scoring.py` - New tool implementation

**Files Modified:**
- `apps/agent/src/pmm_agent/tools/__init__.py` - Added tool import and registration

**Deviations:**
- None - Exercise completed exactly as specified in instructions
- Tool registration followed existing patterns in the codebase
- No modifications to `agent.py` were needed (tools are automatically available via `ALL_TOOLS`)

**Testing:**
- Tool can be tested with: "Am I ready to create positioning? I have a target customer and key differentiator, but no customer proof yet."
- Expected: Agent should recognize the readiness assessment request and call the tool with appropriate boolean arguments

**Reference:**
- Exercise 3 documentation: `docs/EXERCISES.md` (lines 104-254)

---

### Exercise 4: Deploy to Production (Netlify Attempt - Incomplete)

**Status:** ❌ Incomplete - Netlify does not support Python functions

**Context:**
- Exercise 4 requires deploying the agent to production
- Initial attempt used Netlify as specified in `docs/DEPLOYMENT.md`
- Discovered that Netlify Functions do not support Python runtime

**Root Cause: Netlify Language Support Limitations**

**Netlify Functions Supported Languages:**
- ✅ TypeScript
- ✅ JavaScript  
- ✅ Go
- ❌ **Python (NOT SUPPORTED)**

**Documentation Discrepancy:**
- `docs/DEPLOYMENT.md` (lines 68-218) provides detailed instructions for deploying Python/FastAPI applications to Netlify
- Documentation includes Python-specific configuration (`PYTHON_VERSION = "3.11"` in `netlify.toml`)
- Documentation shows Python function wrapper using Mangum for AWS Lambda compatibility
- **However, Netlify's official documentation states functions only support TypeScript, JavaScript, and Go**

**What We Discovered:**
1. **Netlify Functions Language Support**: According to Netlify's official documentation, serverless functions only support TypeScript, JavaScript, and Go. Python is not supported.
2. **Deployment Attempt Results**: 
   - Frontend deployed successfully to Netlify
   - Function deployment showed "No functions deployed" in deploy summary
   - All function files were created correctly (`netlify/functions/agent.py`, `requirements.txt`)
   - Netlify did not recognize Python files as deployable functions
3. **Why It Partially Worked with Localhost**:
   - Frontend was deployed to Netlify (remote)
   - Backend was still running locally on `localhost:8123`
   - Frontend code defaulted to `localhost:8123` because `VITE_API_URL` was empty
   - Browser's "local network" permission allowed remote frontend to connect to local backend
   - This created a hybrid setup: remote frontend → local backend
   - When permission was blocked, connection failed (expected behavior)

**Files Created (But Not Functional on Netlify):**
- `netlify.toml` - Netlify configuration
- `netlify/functions/agent.py` - Python function wrapper (not deployable)
- `netlify/functions/requirements.txt` - Python dependencies
- `apps/web/src/vite-env.d.ts` - TypeScript definitions for Vite env vars
- Updated `apps/agent/src/pmm_agent/server.py` - Health endpoint format
- Updated `apps/web/src/App.tsx` - API URL configuration for production

**Issues Encountered:**
1. **Import Path Error**: Fixed path calculation in `netlify/functions/agent.py` (line 12)
   - Original: `Path(__file__).parent.parent / "apps" / "agent" / "src"` (incorrect - only went up 2 levels)
   - Fixed: `Path(__file__).parent.parent.parent / "apps" / "agent" / "src"` (correct - goes up 3 levels to project root)
2. **Function Not Deploying**: Netlify doesn't recognize Python files as functions
3. **404 Errors**: All API endpoints return 404 because function doesn't exist
   - `/api/health` → redirects to `/.netlify/functions/agent/health` → 404 (function not found)
   - `/api/chat/stream` → redirects to `/.netlify/functions/agent/chat/stream` → 404 (function not found)

**Resolution:**
- Switching to Vercel deployment (supports Python serverless functions)
- Netlify deployment guide in `docs/DEPLOYMENT.md` appears to be incorrect or outdated
- Alternative platforms that support Python: Vercel, Railway, Render, Fly.io, AWS Lambda

**Reference:**
- Exercise 4 documentation: `docs/EXERCISES.md` (lines 254-317)
- Netlify Functions documentation: [Netlify Functions Overview](https://docs.netlify.com/functions/overview/)
- Netlify language support: TypeScript, JavaScript, Go only (no Python)

---

## Notes

- These deviations were necessary due to project configuration mismatches, code syntax issues, and API changes
- The fixes ensure the package can be installed in editable mode with `pip install -e .`
- The syntax fix allows the server to start without import errors
- The API fix allows the agent to be created successfully
- The Exercise 2 fixes ensure proper tool execution and response formatting
- The observability system provides critical debugging capabilities for agent behavior
- All other setup steps from Path C (Developer) instructions remain valid

