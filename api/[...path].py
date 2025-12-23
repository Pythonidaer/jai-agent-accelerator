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

# Create the handler that Vercel will invoke
handler = Mangum(app, lifespan="off")

