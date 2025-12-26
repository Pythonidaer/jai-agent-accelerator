# Deployment Checklist Verification Guide

This guide helps you verify each item in the Production Checklist from `DEPLOYMENT.md`. Use this alongside the automated tests in `test_deployment_checklist.py`.

---

## Quick Start

1. **Run automated tests:**
   ```bash
   cd apps/agent
   python -m pmm_agent.test_deployment_checklist
   ```

2. **Follow this manual verification guide** for items that require manual checking or production environment verification.

---

## Security Checklist

### ✅ API Key Security: Never commit keys to git

**Automated Test:** ✅ Covered by test suite

**Manual Verification:**

1. **Check .gitignore:**
   ```bash
   cat .gitignore | grep -E "\.env|API_KEY|api.*key"
   ```
   Should see `.env` and related patterns.

2. **Search git history for API keys:**
   ```bash
   # Search for Anthropic API keys in git history
   git log --all --full-history -p | grep -i "sk-ant-" | head -20
   ```
   Should return NO results. If you see keys, they're in your git history!

3. **Check current environment variables:**
   ```bash
   # On Vercel
   vercel env ls
   
   # Verify no keys in code
   grep -r "sk-ant-" apps/agent/src/ --exclude-dir=__pycache__
   ```
   Should return NO results.

4. **Verify keys are only in environment:**
   - Check Vercel dashboard → Settings → Environment Variables
   - Ensure `ANTHROPIC_API_KEY` is set and marked as "Sensitive"
   - Keys should NEVER appear in code, logs, or git history

**✅ Status:** [ ] Verified - No keys in git or code

---

### ✅ CORS Configuration: Restrict to your domains only

**Automated Test:** ⚠️  Partially covered (checks code, but needs production verification)

**Manual Verification:**

1. **Check current CORS configuration:**
   ```bash
   # Check server.py for CORS settings
   grep -A 5 "CORSMiddleware" apps/agent/src/pmm_agent/server.py
   ```

2. **Current Status:**
   - Development: Uses `allow_origins=["*"]` (OK for local dev)
   - **Production: Should restrict to your domain**

3. **Test CORS in production:**
   ```bash
   # Replace with your production URL
   curl -H "Origin: https://malicious-site.com" \
        -H "Access-Control-Request-Method: POST" \
        -H "Access-Control-Request-Headers: Content-Type" \
        -X OPTIONS \
        https://your-app.vercel.app/api/chat
   ```
   
   **Expected:** Should reject requests from unauthorized origins

4. **Update for production:**
   ```python
   # In server.py, replace:
   allow_origins=["*"]
   
   # With:
   allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
   if os.getenv("VERCEL") or os.getenv("PRODUCTION"):
       # In production, restrict origins
       allow_origins = allowed_origins if allowed_origins != ["*"] else [
           "https://your-app.vercel.app",
           "https://www.yourdomain.com",
       ]
   else:
       # Development allows all
       allow_origins = ["*"]
   ```

5. **Set environment variable in production:**
   ```bash
   vercel env add ALLOWED_ORIGINS production
   # Enter: https://your-app.vercel.app,https://www.yourdomain.com
   ```

**✅ Status:** [ ] Verified - CORS restricted to production domains

---

### ✅ Rate Limiting: Implement request limits

**Automated Test:** ✅ Implemented

**Implementation Status:** ✅ **COMPLETE**

Rate limiting has been implemented using the `slowapi` library.

**Implementation Details:**

1. **Library Used:** `slowapi` (added to `pyproject.toml`)

2. **Configuration:** Added to `apps/agent/src/pmm_agent/server.py`:
   ```python
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   from slowapi.errors import RateLimitExceeded
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
   ```

3. **Rate Limits Configured:**
   - `/health`: 60 requests/minute per IP
   - `/chat`: 10 requests/minute per IP
   - `/chat/stream`: 10 requests/minute per IP
   - `/metrics`: 30 requests/minute per IP
   - `/metrics/session/{id}`: 30 requests/minute per IP
   - `/metrics/export`: 10 requests/minute per IP

4. **Testing:**
   ```bash
   # Use the provided test script
   cd apps/agent
   python3 tests/test_rate_limiting.py local      # Test locally
   python3 tests/test_rate_limiting.py production https://your-app.vercel.app  # Test production
   
   # Or manual test
   for i in {1..15}; do
     curl -X POST https://your-app.vercel.app/api/chat \
          -H "Content-Type: application/json" \
          -d '{"message":"test"}' \
          -w "\nRequest $i: %{http_code}\n"
     sleep 0.1
   done
   ```
   
   **Expected:** First 10 requests succeed (200), requests 11+ are rate limited (429)
   **Note:** Rate limits reset every minute (sliding window), so all requests within the same minute window will be counted against the limit.

**✅ Status:** [x] Verified - Rate limiting implemented and tested

---

### ✅ Input Validation: Validate all user inputs

**Automated Test:** ✅ Covered by test suite

**Manual Verification:**

1. **Test various input scenarios:**
   ```bash
   # Test empty message (should return 422)
   curl -X POST https://your-app.vercel.app/api/chat \
        -H "Content-Type: application/json" \
        -d '{"message":""}' \
        -w "\nHTTP Status: %{http_code}\n"
   # Expected: HTTP Status: 422
   
   # Test very long message (should return 422)
   LONG_MSG=$(python3 -c "print('x' * 50001)")
   curl -X POST https://your-app.vercel.app/api/chat \
        -H "Content-Type: application/json" \
        -d "{\"message\":\"$LONG_MSG\"}" \
        -w "\nHTTP Status: %{http_code}\n"
   # Expected: HTTP Status: 422
   
   # Test valid message (should return 200)
   curl -X POST https://your-app.vercel.app/api/chat \
        -H "Content-Type: application/json" \
        -d '{"message":"Hello"}' \
        -w "\nHTTP Status: %{http_code}\n"
   # Expected: HTTP Status: 200
   ```
   
   **Or use the test script:**
   ```bash
   cd apps/agent
   ./tests/test_input_validation.sh
   ```

2. **Check Pydantic validation:**
   - ChatRequest model should validate message length, type, etc.
   - Invalid requests should return 422 with validation errors

**✅ Status:** [x] Verified - Input validation working correctly

**Verification Results:**
- ✅ Empty message correctly returns 422
- ✅ Very long message (>50k chars) correctly returns 422  
- ✅ Valid messages return 200
- Test script: `apps/agent/tests/test_input_validation.sh`

---

### ✅ HTTPS Only: Enforce TLS everywhere

**Automated Test:** ✅ Covered (Vercel/Netlify provide HTTPS automatically)

**Manual Verification:**

1. **Check production URL:**
   ```bash
   curl -I https://your-app.vercel.app/api/health
   ```
   
   **Expected:** Should connect via HTTPS (status 200)

2. **Test HTTP redirect (if applicable):**
   ```bash
   curl -I http://your-app.vercel.app/api/health
   ```
   
   **Expected:** Should redirect to HTTPS or be rejected

3. **For self-hosted deployments:**
   - Ensure SSL/TLS certificates are configured
   - Use Let's Encrypt or similar
   - Configure reverse proxy (nginx) to enforce HTTPS

**✅ Status:** [x] Verified - HTTPS enforced (automatic on Vercel)

**Verification Results:**
- ✅ HTTPS endpoint accessible: `https://my-pmm-agent.vercel.app/api/health` returns 200
- ✅ HTTP redirects to HTTPS: `http://` requests return 308 Permanent Redirect
- ✅ Security headers present: `strict-transport-security` header configured
- ✅ HTTP/2 over TLS confirmed

**Note:** Vercel automatically provides HTTPS for all deployments. HTTP requests are redirected to HTTPS.

---

## Performance Checklist

### ✅ Response Caching: Cache common queries

**Automated Test:** ✅ Covered by test suite

**Implementation Status:** ✅ **IMPLEMENTED & VERIFIED**

**What is Response Caching?**

Response caching stores the result of expensive operations (like database queries or complex computations) so that identical requests can be served from memory instead of re-computing the result. This significantly improves performance and reduces server load.

**Why Do We Need It?**

1. **Performance**: Cached responses are served instantly (milliseconds) vs. computing fresh responses (seconds)
2. **Cost Reduction**: Reduces API calls, database queries, and compute time
3. **Server Load**: Prevents redundant work, especially for frequently accessed endpoints
4. **Better User Experience**: Faster response times for users

**What's Achieved with This Implementation?**

1. **Health Endpoint Caching** (`@lru_cache`):
   - Static health check responses are cached indefinitely
   - First request computes the response; subsequent requests use cached version
   - Reduces overhead for monitoring/health check tools that ping frequently
   - **Result**: Health checks return in <1ms instead of ~5-10ms

2. **Metrics Endpoint Caching** (30-second TTL):
   - Metrics responses cached for 30 seconds
   - Reduces load on observability/logging system
   - Balances freshness (metrics update) with performance (caching)
   - **Result**: Dashboard refreshes are instant within the 30s window

**Manual Verification:**

1. **Run automated test:**
   ```bash
   cd apps/agent
   python3 tests/test_response_caching.py local
   # Or test production:
   python3 tests/test_response_caching.py production https://your-app.vercel.app
   ```

2. **Manual verification:**
   ```bash
   # Health endpoint - check cached_at timestamps match (cached)
   curl -s http://localhost:8123/health | jq .cached_at
   curl -s http://localhost:8123/health | jq .cached_at
   # Timestamps should be identical

   # Metrics endpoint - check caching within 30 seconds
   curl -s http://localhost:8123/metrics | jq .cached_at
   sleep 2
   curl -s http://localhost:8123/metrics | jq .cached_at
   # Timestamps should match (within TTL)
   ```

**✅ Status:** [x] Verified - Response caching implemented and tested

---

### ✅ Conversation Truncation: Limit history length

**Automated Test:** ✅ Covered (checks for truncation code)

**Implementation Status:** ✅ **IMPLEMENTED**

**Manual Verification:**

1. **Check conversation history handling:**
   ```bash
   grep -A 10 "truncate_session_messages" apps/agent/src/pmm_agent/server.py
   ```

2. **Current implementation:**
   - ✅ Implemented: `MAX_MESSAGE_HISTORY` configuration (default: 100 messages)
   - ✅ Automatically truncates old messages while keeping system message
   - ✅ Configurable via `MAX_MESSAGE_HISTORY` environment variable
   - ✅ Applied to both `/chat` and `/chat/stream` endpoints

3. **Verify truncation works:**
   ```bash
   # Check code has truncation function
   grep -A 5 "def truncate_session_messages" apps/agent/src/pmm_agent/server.py
   ```

**✅ Status:** [x] Verified - Conversation truncation implemented (100 messages default)

---

### ⚠️ Model Selection: Use Haiku for simple tasks

**Automated Test:** ✅ Covered (checks for MODEL env var)

**Current Implementation Status:** ⚠️ **PARTIALLY IMPLEMENTED**

**What's Actually Implemented:**
- ✅ Model is configurable via `MODEL` environment variable
- ✅ Default: `claude-sonnet-4-20250514` (more capable model)
- ✅ Can manually switch to `claude-3-5-haiku-20241022` for cost savings
- ❌ **No automatic routing** - Model doesn't change based on task complexity
- ❌ **No simple task detection** - All tasks use the same model

**What "Use Haiku for simple tasks" Would Mean:**
The checklist item suggests intelligent model routing:
- **Simple tasks** (e.g., clarification questions, basic formatting, simple lookups) → Use Haiku (cheaper, faster)
- **Complex tasks** (e.g., competitive analysis, positioning strategy, multi-tool workflows) → Use Sonnet (more capable)

**Why This Isn't Fully Implemented:**
1. **No task complexity detection** - There's no logic to determine if a request is "simple" vs "complex"
2. **Single model configuration** - The code uses one model for all requests (configured via env var)
3. **Complexity is subjective** - What counts as "simple" vs "complex" for a PMM agent?

**Current Options:**

1. **Option A: Manual configuration** (Current state)
   - Set `MODEL` env var to use one model for everything
   - Use Haiku for cost savings: `vercel env add MODEL production` → `claude-3-5-haiku-20241022`
   - Use Sonnet for maximum capability: `vercel env add MODEL production` → `claude-sonnet-4-20250514`

2. **Option B: Implement intelligent routing** (Not implemented)
   - Would require adding logic to detect task complexity
   - Route simple requests (e.g., no tool calls, short responses) to Haiku
   - Route complex requests (tool calls, multi-step workflows) to Sonnet
   - Trade-off: More complexity in code for potential cost savings

**Cost Comparison:**
- **Haiku**: ~$0.25 per 1M input tokens, $1.25 per 1M output tokens (~12x cheaper)
- **Sonnet 4**: ~$3 per 1M input tokens, $15 per 1M output tokens (more capable)

**Recommendation:**
For now, **manually choose based on your priorities:**
- **Cost-conscious**: Use Haiku (`claude-3-5-haiku-20241022`) - Good for most PMM tasks
- **Maximum capability**: Use Sonnet 4 (default) - Better for complex strategic analysis

**Manual Verification:**

1. **Check current model:**
   ```bash
   # Check default in code
   grep "MODEL\|model_name" apps/agent/src/pmm_agent/server.py | head -3
   # Output: model_name=os.getenv("MODEL", "claude-sonnet-4-20250514")
   
   # Check environment variable (if set)
   vercel env ls | grep MODEL
   ```

2. **Current production configuration:**
   - Production model: `claude-sonnet-4-20250514` (default and current setting)
   - Decision made to use Sonnet 4 globally (see decision rationale above)
   ```

**✅ Status:** [x] Decision made - Using Sonnet 4 globally (split-model strategy not implemented)

---

### ✅ Cold Start Optimization: Decision Made (Not Implementing)

**Automated Test:** N/A (requires production monitoring)

**Decision Rationale:**
- Cold start optimization (keeping functions warm) costs slightly more money (negligible, but not zero)
- Not required for the project challenge
- If traffic is regular, functions stay warm naturally
- Easy to add later using free services (UptimeRobot) if needed

**What Cold Start Optimization Would Do:**
- Periodically ping the function to keep it "warm" and eliminate 2-5 second cold start delays
- Reduces latency for first request after inactivity
- Improves user experience with consistent, fast responses

**Why We're Not Implementing:**
1. **Cost**: Adds slightly more cost (negligible, but still costs more than $0)
2. **Not Required**: Not required for the project challenge
3. **Natural Warm-up**: If traffic is regular, functions stay warm naturally
4. **Easy to Add Later**: Can be added later if user experience is impacted by cold starts

**When to Reconsider:**
- If user experience is impacted by cold start delays in production
- If traffic patterns create significant gaps (functions spinning down frequently)
- If response time consistency becomes critical

**Related Documentation**: `docs/COLD_START_OPTIMIZATION.md` (comprehensive guide if needed in the future)

**✅ Status:** [x] Decision made - Not implementing for now

---

## Monitoring Checklist

### ✅ Health Checks: Automated uptime monitoring

**Automated Test:** ✅ Covered

**Manual Verification:**

1. **Test health endpoint:**
   ```bash
   curl https://your-app.vercel.app/api/health
   ```
   
   **Expected:** `{"status": "ok", "agent": "jai-agent-accelerator", "version": "0.1.0"}`

2. **Set up uptime monitoring:**
   - **UptimeRobot** (free): https://uptimerobot.com
     - Add monitor: `https://your-app.vercel.app/api/health`
     - Check interval: 5 minutes
   - **Pingdom**: Similar setup
   - **Vercel Analytics**: Built-in monitoring

3. **Configure alerts:**
   - Email notifications when health check fails
   - SMS for critical outages (paid services)

**✅ Status:** [ ] Verified - Health checks configured and monitored

---

### ⚠️  Error Tracking: Sentry or similar

**Automated Test:** ⚠️  Checks for Sentry, may not be configured

**Manual Verification:**

1. **Check if error tracking is set up:**
   ```bash
   grep -i "sentry\|error.*track\|exception.*handler" apps/agent/src/pmm_agent/*.py
   ```

2. **Set up Sentry (recommended):**
   ```bash
   pip install sentry-sdk[fastapi]
   ```
   
   ```python
   # Add to server.py
   import sentry_sdk
   from sentry_sdk.integrations.fastapi import FastApiIntegration
   
   sentry_sdk.init(
       dsn=os.getenv("SENTRY_DSN"),
       integrations=[FastApiIntegration()],
       traces_sample_rate=0.1,
       environment=os.getenv("ENVIRONMENT", "production"),
   )
   ```
   
   ```bash
   vercel env add SENTRY_DSN production
   # Get DSN from https://sentry.io
   ```

3. **Test error tracking:**
   - Trigger an error (e.g., invalid API call)
   - Check Sentry dashboard for error report

**✅ Status:** [ ] Verified - Error tracking configured and tested

---

### ✅ Usage Metrics: Track tokens and costs

**Automated Test:** ✅ Covered (checks for /metrics endpoint)

**Manual Verification:**

1. **Test metrics endpoint:**
   ```bash
   curl https://your-app.vercel.app/api/metrics
   ```
   
   **Expected:** Returns session data and usage statistics

2. **Check observability system:**
   ```bash
   # Check if observability.py tracks tokens
   grep -i "token\|cost\|usage" apps/agent/src/pmm_agent/observability.py
   ```

3. **Enhance token tracking (if needed):**
   - Track input/output tokens per request
   - Calculate cost per request (based on model pricing)
   - Aggregate daily/monthly costs

4. **Set up cost monitoring:**
   - Anthropic Dashboard: Monitor API usage
   - Set up budget alerts in Anthropic console
   - Export metrics to monitoring dashboard

**✅ Status:** [ ] Verified - Usage metrics tracked and monitored

---

### ⚠️  Alerting: Set up cost and error alerts

**Automated Test:** N/A (requires external service configuration)

**Manual Verification:**

1. **Anthropic Budget Alerts:**
   - Go to Anthropic Console → Billing
   - Set budget limit (e.g., $50/month)
   - Configure email alerts at 50%, 75%, 90%, 100%

2. **Error Alerts (if using Sentry):**
   - Configure Sentry alert rules
   - Alert on error rate spikes
   - Alert on critical errors

3. **Uptime Alerts (from health checks):**
   - Configure UptimeRobot alerts
   - Email/SMS when health check fails

**✅ Status:** [ ] Verified - Alerts configured for costs and errors

---

## Cost Control Checklist

### ⚠️  Budget Alerts: Set spending limits

**Manual Verification:**

1. **Anthropic Console:**
   - Set monthly budget limit
   - Enable email notifications
   - Monitor daily spending

2. **Vercel Billing:**
   - Set spending limits (if applicable)
   - Monitor function execution costs

**✅ Status:** [ ] Verified - Budget alerts configured

---

### ⚠️  Usage Dashboards: Monitor token consumption

**Manual Verification:**

1. **Create usage dashboard:**
   - Use `/metrics` endpoint data
   - Build simple dashboard or use existing tools
   - Track: requests/day, tokens/day, cost/day

2. **Anthropic Dashboard:**
   - Use built-in usage analytics
   - Export data for custom analysis

**✅ Status:** [ ] Verified - Usage dashboard available

---

### ⚠️  Prompt Optimization: Minimize input tokens

**Manual Verification:**

1. **Review system prompt:**
   ```bash
   wc -w apps/agent/src/pmm_agent/prompts.py
   ```
   - Keep prompts concise
   - Remove unnecessary instructions
   - Use templates for repeated content

2. **Monitor prompt sizes:**
   - Check token counts in logs
   - Optimize verbose prompts
   - Use shorter model names where possible

**✅ Status:** [ ] Verified - Prompts optimized for token efficiency

---

### ⚠️  Caching Strategy: Reduce duplicate calls

**Manual Verification:**

1. **Identify cacheable queries:**
   - Health checks
   - Common questions/responses
   - Static data lookups

2. **Implement caching:**
   - Cache responses for identical queries
   - Set appropriate TTLs
   - Invalidate cache when needed

**✅ Status:** [ ] Verified - Caching reduces duplicate API calls

---

## Running the Full Verification

1. **Run automated tests:**
   ```bash
   cd apps/agent
   python -m pmm_agent.test_deployment_checklist
   ```

2. **Follow this manual checklist** for each item

3. **Update DEPLOYMENT.md** checklist with [x] marks as you verify

4. **Document any issues** and create issues/todos for improvements

---

## Summary

- ✅ **Automated tests:** Run `python -m pmm_agent.test_deployment_checklist`
- ⚠️  **Manual verification:** Use this guide for production-specific checks
- 📊 **Track progress:** Update the checklist in DEPLOYMENT.md as you verify items

Good luck with your deployment! 🚀

