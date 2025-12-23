# Troubleshooting Guide

> When things go wrong, start here.

This guide covers common issues organized by exercise and a dependency reference for deployment.

---

## Quick Fixes by Exercise

### Exercise 1: Hello, Agent

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ANTHROPIC_API_KEY not set` | Environment variable missing | `export ANTHROPIC_API_KEY=sk-ant-your-key` |
| `Port 8123 already in use` | Previous process running | `lsof -ti:8123 \| xargs kill` |
| `ModuleNotFoundError` | Virtual environment not activated | `source .venv/bin/activate` |
| `pip install` fails | Wrong Python version | Ensure Python 3.11+: `python3 --version` |
| Frontend can't connect | Backend not running | Start backend first, then frontend |
| CORS error in browser | Backend on wrong host | Use `--host 0.0.0.0` flag |

**Still stuck?** Run the diagnostic:
```bash
# Check Python version
python3 --version  # Should be 3.11+

# Check Node version
node --version  # Should be 18+

# Check API key is set
echo $ANTHROPIC_API_KEY  # Should show sk-ant-...

# Check ports are free
lsof -i:8123  # Should be empty
lsof -i:3003  # Should be empty
```

---

### Exercise 2: Prompt Surgery

| Symptom | Cause | Fix |
|---------|-------|-----|
| Changes not appearing | Didn't restart server | Restart uvicorn after prompt changes |
| Agent ignoring instruction | Instruction buried too deep | Move instruction earlier in prompt |
| `SyntaxError` in Python | String formatting issue | Check for matching quotes, proper escapes |
| Agent behavior erratic | Conflicting instructions | Review full prompt for contradictions |

**Prompt debugging technique:**
```python
# Add this to see what prompt is being used
print(MAIN_SYSTEM_PROMPT[:500])  # First 500 chars
```

---

### Exercise 3: Build Your First Tool

| Symptom | Cause | Fix |
|---------|-------|-----|
| Tool not appearing | Not registered in agent.py | Add to TOOLS list in agent.py |
| Agent never uses tool | Docstring too vague | Make docstring more specific about when to use |
| `TypeError` at runtime | Pydantic model mismatch | Ensure return matches schema |
| Tool called but returns None | Missing return statement | Add explicit return |

**Tool debugging technique:**
```python
# Test tool directly without agent
from pmm_agent.tools.your_tool import your_function
result = your_function("test input")
print(result)
```

---

### Exercise 4: Deploy to Production

#### Netlify Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Build fails on Netlify | Node/Python version mismatch | Set in `netlify.toml` (see below) |
| Function not found | Wrong path in redirects | Check `netlify.toml` paths match |
| `ANTHROPIC_API_KEY` undefined | Env var not set in Netlify | `netlify env:set ANTHROPIC_API_KEY sk-ant-...` |
| Function timeout (10s) | Free tier limit | Upgrade Netlify or optimize response |
| CORS error in production | `ALLOWED_ORIGINS` wrong | Set to your domain or `*` for testing |
| Cold start > 5 seconds | Normal for serverless | Implement keep-warm or use Railway |
| "No functions deployed" | Netlify doesn't support Python | **Use Vercel instead** (see below) |

**Verify Netlify deployment:**
```bash
# Health check
curl https://your-site.netlify.app/api/health

# Expected response
{"status": "ok", "agent": "jai-agent-accelerator"}
```

#### Vercel Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `OSError: Read-only file system` | Logging tries to write to `/var/task` | **Fixed automatically** - observability detects Vercel and uses stdout |
| `FUNCTION_INVOCATION_FAILED` on import | File logging attempted | Check `observability.py` has Vercel detection (should be automatic) |
| `404 NOT_FOUND` on `/api/*` | Rewrite order wrong | API rewrite must come **before** frontend rewrite in `vercel.json` |
| Frontend loads but API 404 | Rewrite catching API routes | Ensure `/api/(.*)` rewrite is first, before `/(.*)` catch-all |
| `ModuleNotFoundError: pmm_agent` | Path setup incorrect | Check `api/index.py` uses `parent.parent` (2 levels up from `api/`) |
| Function crashes on startup | Missing dependencies | Ensure `api/requirements.txt` includes all packages (no Mangum needed) |
| `root_path` error | FastAPI path mismatch | `server.py` automatically sets `root_path="/api"` when `VERCEL` env var is set |

**Verify Vercel deployment:**
```bash
# Health check
curl https://your-project.vercel.app/api/health

# Expected response
{"status": "ok", "agent": "jai-agent-accelerator", "version": "0.1.0"}
```

**Common Vercel debugging steps:**

1. **Check function logs:**
   - Go to Vercel Dashboard → Your Project → Functions → `index`
   - Click on a deployment → View logs
   - Look for import errors or runtime errors

2. **Verify rewrite order:**
   ```json
   "rewrites": [
     { "source": "/api/(.*)", "destination": "/api/index.py" },  // API first!
     { "source": "/(.*)", "destination": "/apps/web/$1" }         // Frontend second
   ]
   ```

3. **Test API directly:**
   ```bash
   curl -v https://your-project.vercel.app/api/health
   # Should return 200, not 404
   ```

4. **Check environment variables:**
   ```bash
   vercel env ls
   # Should show ANTHROPIC_API_KEY
   ```

---

### Exercise 5: Domain Conversion

| Symptom | Cause | Fix |
|---------|-------|-----|
| Config not loading | JSON syntax error | Validate JSON at jsonlint.com |
| Tools not available | Not imported in agent.py | Add import + registration |
| Quick actions not updating | Frontend not rebuilt | `npm run build` in apps/web |
| Domain expertise missing | Prompt not updated | Add domain knowledge to prompts.py |

---

## Dependency Reference

### What You Need Installed

| Dependency | Version | Required For | Install Command |
|------------|---------|--------------|-----------------|
| Python | 3.11+ | Backend | [python.org](https://python.org) |
| Node.js | 18+ | Frontend | [nodejs.org](https://nodejs.org) |
| npm | 9+ | Package management | Comes with Node |
| Git | 2.0+ | Version control | [git-scm.com](https://git-scm.com) |

### API Keys Required

| Service | Purpose | Cost | Get It |
|---------|---------|------|--------|
| **Anthropic** | Claude API | ~$3/1M tokens | [console.anthropic.com](https://console.anthropic.com) |

### Deployment Options

| Platform | Best For | Free Tier | Monthly Cost | Setup Time |
|----------|----------|-----------|--------------|------------|
| **Netlify** | Simple deploy | 125K function calls | $0-25 | 30 min |
| **Railway** | More control | $5 credit | $5-20 | 20 min |
| **Vercel** | React apps | 100K function calls | $0-20 | 25 min |
| **Docker** | Self-hosted | N/A | Your infra | 45 min |

### CI/CD Options

| Service | Purpose | Free Tier | Setup |
|---------|---------|-----------|-------|
| **GitHub Actions** | Auto-deploy on push | 2,000 min/month | See below |
| **Netlify Deploy** | Auto-deploy from GitHub | Included | Connect repo |

---

## For PMs & Designers: Infrastructure Explained

**Why does this matter?**

You built an agent that works on your laptop. But for anyone else to use it, it needs to be:
1. **Hosted** somewhere (not your laptop)
2. **Deployed** automatically when you make changes
3. **Monitored** so you know when it breaks

**The good news:** You can do all of this for free to start.

### Option A: "I Just Want It to Work" (Recommended)

**Use Netlify's automated deployment:**

1. Push code to GitHub
2. Connect Netlify to your GitHub repo
3. Netlify automatically deploys on every push

**Cost:** Free for hobby projects, $19/month for production
**Time:** 30 minutes to set up
**Maintenance:** Near zero

### Option B: "I Want More Control"

**Use Railway with GitHub:**

1. Push code to GitHub
2. Connect Railway to your GitHub repo
3. Railway builds and deploys automatically

**Cost:** $5/month minimum
**Time:** 20 minutes to set up
**Maintenance:** Low

### Option C: "I Want to Understand Everything"

See BUILD_VS_BUY.md for the full breakdown.

---

## Fresh Machine Testing Plan

> How we validate that setup works for new users.

### The Problem

"It works on my machine" doesn't help users. We need to test the setup experience on a clean environment.

### Testing Approach

**Option 1: GitHub Codespaces (Recommended)**
```bash
# Create a new Codespace from the repo
# This gives you a fresh Linux environment

# Run through all exercises
# Document any issues
```

**Option 2: Docker Fresh Environment**
```bash
# Start with base Python image
docker run -it python:3.11-slim /bin/bash

# Clone and test
git clone https://github.com/chai-with-jai/jai-agent-accelerator.git
cd jai-agent-accelerator
# Follow Quick Start from scratch
```

**Option 3: VM (Multipass on Mac)**
```bash
# Create fresh Ubuntu VM
multipass launch --name fresh-test

# SSH in
multipass shell fresh-test

# Install dependencies from scratch
sudo apt update
sudo apt install python3.11 python3-pip nodejs npm git

# Clone and test
git clone https://github.com/chai-with-jai/jai-agent-accelerator.git
```

### What We Test

| Step | Expected Outcome | Pass/Fail |
|------|------------------|-----------|
| Clone repo | Completes without error | ☐ |
| Install Python deps | All packages install | ☐ |
| Install Node deps | All packages install | ☐ |
| Set API key | No errors | ☐ |
| Start backend | Server running on 8123 | ☐ |
| Start frontend | App running on 3003 | ☐ |
| First query | Agent responds | ☐ |
| Exercise 1 | Complete in < 30 min | ☐ |
| Exercise 2 | Complete in < 45 min | ☐ |
| Deploy to Netlify | Live URL works | ☐ |

### Known Environment Issues

| Environment | Issue | Workaround |
|-------------|-------|------------|
| Windows | Path separators | Use WSL2 |
| Mac M1/M2 | Some pip packages | Use `--platform` flag |
| Old Python | Missing features | Upgrade to 3.11+ |
| Corporate proxy | npm/pip blocked | Configure proxy settings |

---

## Error Message Reference

### Python Errors

```
ModuleNotFoundError: No module named 'pmm_agent'
```
**Fix:** Install the package in editable mode:
```bash
cd apps/agent
pip install -e .
```

```
anthropic.AuthenticationError: Invalid API Key
```
**Fix:** Check your API key is correct and exported:
```bash
echo $ANTHROPIC_API_KEY  # Should start with sk-ant-
```

```
pydantic.ValidationError
```
**Fix:** Your tool is returning wrong types. Check the Pydantic model matches the return value.

### Node/Frontend Errors

```
ENOENT: no such file or directory
```
**Fix:** Run `npm install` first:
```bash
cd apps/web
npm install
```

```
fetch failed (CORS)
```
**Fix:** Backend isn't running or is on wrong port. Check:
```bash
curl http://localhost:8123/health
```

### Deployment Errors

```
Function exceeded runtime limit
```
**Fix:** Netlify free tier = 10 seconds. Either:
1. Optimize your agent (shorter prompts, smaller responses)
2. Upgrade to Netlify Pro (26 seconds)
3. Use Railway instead (no timeout)

```
Build failed: Python version not supported
```
**Fix:** Add to `netlify.toml`:
```toml
[build.environment]
  PYTHON_VERSION = "3.11"
```

```
OSError: [Errno 30] Read-only file system: '/var/task/.../logs/agent.log'
```
**Fix:** This happens on Vercel when code tries to write to the deployment directory. The observability system automatically detects Vercel and disables file logging. If you see this error:

1. Check `observability.py` has `running_on_vercel()` function
2. Ensure file logging is disabled when `running_on_vercel()` returns `True`
3. Redeploy - logs will go to stdout/stderr (visible in Vercel dashboard)

**Root cause:** Vercel's `/var/task` directory (where your code lives) is read-only. Only `/tmp` is writable, but for logging, stdout/stderr is preferred.

```
FUNCTION_INVOCATION_FAILED on Vercel
```
**Fix:** Check Vercel function logs for the actual error. Common causes:
1. **Import error:** Path setup in `api/index.py` incorrect - use `parent.parent` (2 levels up)
2. **Missing dependency:** Check `api/requirements.txt` includes all packages
3. **File write attempt:** Logging trying to write files (should be auto-fixed)
4. **Environment variable missing:** `ANTHROPIC_API_KEY` not set in Vercel dashboard

```
404 on /api/* routes on Vercel
```
**Fix:** Rewrite order in `vercel.json` is critical:
```json
"rewrites": [
  { "source": "/api/(.*)", "destination": "/api/index.py" },  // MUST be first
  { "source": "/(.*)", "destination": "/apps/web/$1" }         // Must be second
]
```
The frontend catch-all `/(.*)` will intercept API requests if it comes first!

---

## Getting Human Help

| Issue Type | Channel | Response Time |
|------------|---------|---------------|
| Quick questions | Discord | Hours |
| Setup issues | Email support | 48 hours (Starter) |
| Complex bugs | Priority email | 24 hours (Pro/Team) |
| Strategic questions | Office hours | Weekly (Pro/Team) |

**When asking for help, include:**
1. What you were trying to do
2. The exact error message
3. Your environment (Mac/Windows/Linux, Python version)
4. What you've already tried

---

[← Exercises](EXERCISES.md) | [Build vs Buy →](BUILD_VS_BUY.md) | [Advanced →](ADVANCED.md)
