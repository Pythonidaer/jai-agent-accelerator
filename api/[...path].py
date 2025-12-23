"""
Vercel serverless function wrapper for the PMM Agent.

This wraps our FastAPI app for Vercel's serverless environment.
Uses catch-all routing [...path] to handle all /api/* paths.
"""
import sys
from pathlib import Path

# Add the agent source to Python path
project_root = Path(__file__).parent.parent
agent_src = project_root / "apps" / "agent" / "src"
sys.path.insert(0, str(agent_src))

from mangum import Mangum
from pmm_agent.server import app

# Create Mangum adapter
mangum_handler = Mangum(app, lifespan="off")

# Wrapper to strip /api prefix from path
def handler(event, context):
    # Extract the path from the event
    path = event.get("path", "")
    
    # If path starts with /api/, strip it (FastAPI expects /health, /chat/stream, etc.)
    if path.startswith("/api/"):
        event["path"] = path[4:]  # Remove "/api" prefix
    elif path.startswith("/api"):
        event["path"] = path[4:]  # Remove "/api" prefix (no trailing slash)
    
    # Ensure path starts with / or is empty (default to /)
    if not event["path"] or not event["path"].startswith("/"):
        event["path"] = "/" + event["path"] if event["path"] else "/"
    
    return mangum_handler(event, context)

