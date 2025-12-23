"""
Positioning Readiness Scoring Tool.

Calculates how ready a product is for positioning work.
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List


class ReadinessScore(BaseModel):
    """Structured readiness assessment output."""
    score: int = Field(description="Readiness score 1-10")
    strengths: List[str] = Field(description="What's ready")
    gaps: List[str] = Field(description="What's missing")
    next_action: str = Field(description="Most important next step")


@tool
def calculate_positioning_readiness(
    has_target_customer: bool,
    has_competitive_alternative: bool,
    has_key_differentiator: bool,
    has_customer_proof: bool,
    has_clear_category: bool,
) -> ReadinessScore:
    """
    Calculate how ready a product is for positioning work.

    Use this when a user wants to assess if they're ready
    to create positioning, or what gaps they need to fill first.

    Args:
        has_target_customer: Do they know their ideal customer?
        has_competitive_alternative: Do they know what customers use instead?
        has_key_differentiator: Do they have a unique capability?
        has_customer_proof: Do they have customer evidence/testimonials?
        has_clear_category: Do they know their market category?

    Returns:
        Readiness score with strengths, gaps, and next action
    """
    checks = {
        "Target Customer Definition": has_target_customer,
        "Competitive Alternative Identified": has_competitive_alternative,
        "Key Differentiator Articulated": has_key_differentiator,
        "Customer Proof Available": has_customer_proof,
        "Market Category Defined": has_clear_category,
    }

    strengths = [k for k, v in checks.items() if v]
    gaps = [k for k, v in checks.items() if not v]
    score = len(strengths) * 2  # 0-10 scale

    # Determine next action based on gaps
    if not has_target_customer:
        next_action = "Define your target customer segment first"
    elif not has_competitive_alternative:
        next_action = "Identify what customers use before finding you"
    elif not has_key_differentiator:
        next_action = "Articulate what you have that alternatives don't"
    elif not has_customer_proof:
        next_action = "Collect customer testimonials and use cases"
    elif not has_clear_category:
        next_action = "Define your market category"
    else:
        next_action = "You're ready to create positioning!"

    return ReadinessScore(
        score=score,
        strengths=strengths,
        gaps=gaps,
        next_action=next_action,
    )


# Export for agent
SCORING_TOOLS = [calculate_positioning_readiness]

