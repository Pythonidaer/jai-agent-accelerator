# Exercise 4: Deploy to Production - Gameplan

## Status: ✅ Files Prepared - Ready for Human Steps

All deployment files have been created and are ready. The following steps require human input.

---

## ✅ Completed (Automated Prep Work)

### Files Created:
1. ✅ **`netlify.toml`** - Netlify configuration in project root
   - Build commands for frontend
   - Function directory configuration
   - API route redirects
   - SPA fallback routing

2. ✅ **`apps/agent/netlify/functions/agent.py`** - Netlify function wrapper
   - Wraps FastAPI app with Mangum for Lambda compatibility
   - Sets up Python path correctly

3. ✅ **`apps/agent/netlify/functions/requirements.txt`** - Function dependencies
   - Includes Mangum, Anthropic, LangChain, FastAPI, and all required packages
   - Version constraints match `pyproject.toml`

4. ✅ **`apps/web/.env.production`** - Frontend production environment
   - Empty `VITE_API_URL` (uses relative URLs with Netlify redirects)

5. ✅ **Health Endpoint Updated** - `apps/agent/src/pmm_agent/server.py`
   - Changed from `{"status": "ok", "agent": "pmm-deep-agent"}`
   - To: `{"status": "ok", "agent": "jai-agent-accelerator", "version": "0.1.0"}`
   - Matches expected format from Exercise 4

---

## 🔴 Human Input Required

### Step 1: GitHub Repository Setup
**Action:** Ensure your code is pushed to GitHub
```bash
# If not already done:
git add .
git commit -m "Prepare for Exercise 4 deployment"
git push origin main
```
**Status:** ⏳ Waiting for user

---

### Step 2: Install Netlify CLI
**Action:** Install and login to Netlify
```bash
npm install -g netlify-cli
netlify login
```
**Notes:**
- This will open a browser for authentication
- You'll need a Netlify account (free tier is fine)
- **Status:** ⏳ Waiting for user

---

### Step 3: Initialize Netlify Project
**Action:** Run Netlify initialization
```bash
netlify init
```
**When prompted:**
- Choose: "Create & configure a new site"
- Select your team (or create one)
- Set site name (e.g., `my-pmm-agent` or `jai-agent-accelerator`)
- This will create a `.netlify` directory with site configuration

**Status:** ⏳ Waiting for user

---

### Step 4: Set Environment Variables
**Action:** Set your Anthropic API key
```bash
netlify env:set ANTHROPIC_API_KEY sk-ant-your-actual-key-here
```
**Notes:**
- Replace `sk-ant-your-actual-key-here` with your actual API key
- You can verify with: `netlify env:list`
- **Status:** ⏳ Waiting for user

---

### Step 5: Deploy to Production
**Action:** Deploy the site
```bash
netlify deploy --prod
```
**Notes:**
- This will build the frontend and deploy functions
- First deployment may take 3-5 minutes
- You'll get a URL like: `https://your-site-name.netlify.app`
- **Status:** ⏳ Waiting for user

---

### Step 6: Verify Deployment
**Action:** Test the deployment
```bash
# Health check
curl https://your-site.netlify.app/api/health

# Expected response:
# {"status": "ok", "agent": "jai-agent-accelerator", "version": "0.1.0"}
```

**Then:**
1. Open `https://your-site.netlify.app` in browser
2. Test a conversation with the agent
3. Verify it works end-to-end

**Status:** ⏳ Waiting for user

---

### Step 7: Share Success
**Action:** Post in Discord
```
Exercise 4 complete! My agent is live at https://your-site.netlify.app
```

**Status:** ⏳ Waiting for user

---

## 📋 Pre-Deployment Checklist

Before running `netlify deploy --prod`, verify:

- [ ] All files are committed to git
- [ ] `netlify.toml` exists in project root
- [ ] `apps/agent/netlify/functions/agent.py` exists
- [ ] `apps/agent/netlify/functions/requirements.txt` exists
- [ ] `apps/web/.env.production` exists
- [ ] Health endpoint returns correct format
- [ ] Netlify CLI is installed (`netlify --version`)
- [ ] You're logged into Netlify (`netlify status`)
- [ ] Environment variable is set (`netlify env:list`)

---

## 🐛 Troubleshooting

### Build Fails
- Check `package.json` and `pyproject.toml` are valid
- Verify Node.js 18+ is available
- Check build logs: `netlify logs`

### Function Not Found
- Verify `netlify.toml` redirects are correct
- Check function directory path matches config
- Ensure `agent.py` is in `apps/agent/netlify/functions/`

### Environment Variable Missing
- Use `netlify env:list` to verify
- Re-run `netlify env:set ANTHROPIC_API_KEY sk-ant-...`
- Check function logs for errors

### Timeout Errors
- Netlify free tier = 10 second limit
- Complex queries may timeout
- Consider upgrading to Netlify Pro (26 seconds) if needed

### CORS Errors
- Check frontend is using relative URLs
- Verify `VITE_API_URL` is empty in `.env.production`
- Netlify redirects handle CORS automatically

---

## 📚 Reference

- **Exercise 4:** `docs/EXERCISES.md` (lines 254-317)
- **Deployment Guide:** `docs/DEPLOYMENT.md`
- **Troubleshooting:** `docs/TROUBLESHOOTING.md` (lines 74-96)

---

## 🎯 Success Criteria

- [ ] Agent accessible at public URL
- [ ] HTTPS enabled (automatic with Netlify)
- [ ] Health check returns `{"status": "ok", "agent": "jai-agent-accelerator", "version": "0.1.0"}`
- [ ] Can have a conversation through the web interface
- [ ] URL shared in Discord

---

**Next Steps:** Follow the "Human Input Required" steps above in order. All files are ready!

