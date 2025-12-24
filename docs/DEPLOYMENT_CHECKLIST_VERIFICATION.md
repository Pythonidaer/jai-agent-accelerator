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

### ⚠️  Rate Limiting: Implement request limits

**Automated Test:** ❌ Not implemented yet

**Manual Verification:**

1. **Check if rate limiting exists:**
   ```bash
   grep -i "rate.*limit\|limiter\|slowapi" apps/agent/src/pmm_agent/server.py
   ```

2. **If not implemented, add rate limiting:**

   **Option A: Using slowapi (Recommended)**
   ```bash
   pip install slowapi
   ```
   
   ```python
   # Add to server.py
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   from slowapi.errors import RateLimitExceeded
   
   limiter = Limiter(key_func=get_remote_address, app=app)
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
   
   # Add to endpoints
   @app.post("/chat")
   @limiter.limit("10/minute")  # 10 requests per minute
   async def chat(request: Request, chat_request: ChatRequest):
       # ... existing code
   ```

   **Option B: Vercel Edge Config (Platform-level)**
   - Use Vercel's built-in rate limiting in `vercel.json`
   - Configure via Vercel dashboard

3. **Test rate limiting:**
   ```bash
   # Make rapid requests
   for i in {1..15}; do
     curl -X POST https://your-app.vercel.app/api/chat \
          -H "Content-Type: application/json" \
          -d '{"message":"test"}' &
   done
   wait
   ```
   
   **Expected:** Some requests should be rate limited (429 status)

**✅ Status:** [ ] Verified - Rate limiting implemented and tested

---

### ✅ Input Validation: Validate all user inputs

**Automated Test:** ✅ Covered by test suite

**Manual Verification:**

1. **Test various input scenarios:**
   ```bash
   # Test empty message
   curl -X POST https://your-app.vercel.app/api/chat \
        -H "Content-Type: application/json" \
        -d '{"message":""}'
   # Should return 422 or 400
   
   # Test very long message
   curl -X POST https://your-app.vercel.app/api/chat \
        -H "Content-Type: application/json" \
        -d "{\"message\":\"$(python -c 'print("x"*100000)')\"}"
   # Should handle gracefully (reject or truncate)
   
   # Test SQL injection attempt
   curl -X POST https://your-app.vercel.app/api/chat \
        -H "Content-Type: application/json" \
        -d '{"message":"'\'' OR 1=1--"}'
   # Should be treated as normal text (safe)
   ```

2. **Check Pydantic validation:**
   - ChatRequest model should validate message length, type, etc.
   - Invalid requests should return 422 with validation errors

**✅ Status:** [ ] Verified - Input validation working correctly

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

**✅ Status:** [ ] Verified - HTTPS enforced (automatic on Vercel)

---

## Performance Checklist

### ⚠️  Response Caching: Cache common queries

**Automated Test:** ⚠️  Checks for caching code, but may not be implemented

**Manual Verification:**

1. **Check if caching is implemented:**
   ```bash
   grep -i "cache\|lru_cache\|redis" apps/agent/src/pmm_agent/server.py
   ```

2. **Consider implementing:**
   - Cache common queries/responses
   - Use in-memory cache for simple cases
   - Use Redis for distributed caching (if needed)

3. **Example implementation:**
   ```python
   from functools import lru_cache
   from datetime import datetime, timedelta
   
   # Simple cache for health checks
   @lru_cache(maxsize=128)
   def cached_health_check():
       return {"status": "ok", "timestamp": datetime.now().isoformat()}
   ```

**✅ Status:** [ ] Verified - Caching implemented where appropriate

---

### ⚠️  Conversation Truncation: Limit history length

**Automated Test:** ⚠️  Checks for truncation code, may not be implemented

**Manual Verification:**

1. **Check conversation history handling:**
   ```bash
   grep -A 10 "session\[.messages.\]" apps/agent/src/pmm_agent/server.py
   ```

2. **Current behavior:**
   - Sessions store all messages
   - Long conversations may exceed token limits or cause performance issues

3. **Implement truncation:**
   ```python
   MAX_MESSAGES = 50  # Keep last 50 messages
   
   def truncate_messages(messages):
       # Keep system message + last N user/assistant pairs
       if len(messages) > MAX_MESSAGES:
           return [messages[0]] + messages[-MAX_MESSAGES:]
       return messages
   ```

4. **Test with long conversation:**
   - Have a conversation with 100+ messages
   - Verify it still works and response time is reasonable

**✅ Status:** [ ] Verified - Conversation truncation implemented

---

### ✅ Model Selection: Use Haiku for simple tasks

**Automated Test:** ✅ Covered (checks for MODEL env var)

**Manual Verification:**

1. **Check current model:**
   ```bash
   # In server.py, check default model
   grep "MODEL\|model_name" apps/agent/src/pmm_agent/server.py
   ```

2. **Consider model optimization:**
   - Use `claude-3-5-haiku-20241022` for simple queries
   - Use `claude-sonnet-4-20250514` for complex analysis
   - Switch based on request complexity or user preference

3. **Set model in production:**
   ```bash
   vercel env add MODEL production
   # Enter: claude-3-5-haiku-20241022 (for cost optimization)
   ```

**✅ Status:** [ ] Verified - Model selection configured appropriately

---

### ⚠️  Cold Start Optimization: Keep functions warm

**Automated Test:** N/A (requires production monitoring)

**Manual Verification:**

1. **Monitor cold starts:**
   - Check Vercel function logs for cold start times
   - First request after inactivity may take 1-3 seconds

2. **Optimize cold starts:**
   - Minimize dependencies
   - Use smaller Python packages when possible
   - Consider Vercel Pro for better performance

3. **Keep functions warm (optional):**
   - Set up a cron job to ping health endpoint every 5 minutes
   - Use services like UptimeRobot for health checks (side effect: keeps functions warm)

**✅ Status:** [ ] Verified - Cold starts monitored and optimized

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

