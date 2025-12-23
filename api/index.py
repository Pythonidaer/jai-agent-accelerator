"""
Vercel serverless function for PMM Agent.

Vercel's native FastAPI support - no Mangum needed!
Vercel automatically adapts the FastAPI app instance.
"""
import sys
from pathlib import Path

# Ensure Vercel can import your backend module
# From api/index.py, go up to project root, then to apps/agent/src
ROOT = Path(__file__).resolve().parent.parent
agent_src = ROOT / "apps" / "agent" / "src"
sys.path.insert(0, str(agent_src))

from pmm_agent.server import app  # exports FastAPI app

# Vercel will automatically handle the adaptation
# No need for Mangum or custom handler

