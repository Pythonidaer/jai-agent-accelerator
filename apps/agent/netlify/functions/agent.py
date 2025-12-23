"""
Netlify serverless function wrapper for the PMM Agent.

This wraps our FastAPI app with Mangum for AWS Lambda compatibility
(which Netlify Functions use under the hood).
"""
import sys
from pathlib import Path

# Add the agent source to Python path
agent_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(agent_src))

from mangum import Mangum
from pmm_agent.server import app

# Create the handler that Netlify will invoke
handler = Mangum(app, lifespan="off")

