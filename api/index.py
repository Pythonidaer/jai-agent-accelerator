"""
Vercel serverless function for PMM Agent.

Vercel's native FastAPI support - no Mangum needed!
Vercel automatically adapts the FastAPI app instance.
"""
import sys
from pathlib import Path

# Ensure Vercel can import your backend module
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "apps" / "agent" / "src"))

from pmm_agent.server import app  # exports FastAPI app

# Vercel will automatically handle the adaptation
# No need for Mangum or custom handler

