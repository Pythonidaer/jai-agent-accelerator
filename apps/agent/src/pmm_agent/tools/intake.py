"""
Intake Tools - Product Analysis and Requirements Extraction.

These tools help structure and understand the product context
before diving into positioning and messaging work.
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional


class ProductAnalysis(BaseModel):
    """Structured product analysis output."""
    product_name: str
    category: str
    target_audience: str
    core_problem: str
    key_features: list[str]
    differentiators: list[str]
    proof_points: list[str]
    unknowns: list[str]


@tool
def analyze_product(
    product_description: str,
    existing_materials: Optional[str] = None,
) -> str:
    """
    Analyze a product to extract structured information for positioning work.

    Use this tool when starting any PMM project to structure the inputs
    and identify gaps in the available information.

    IMPORTANT: The product_description parameter MUST be extracted from the user's message.
    Look at the most recent user message in the conversation and extract the product description from there.
    If the user described their product, use that description. If they mentioned a product name and what it does, include both.

    Args:
        product_description: REQUIRED - The full description of the product from the user's message. 
                             Extract this from the conversation context, including what the product does,
                             who it's for, and what problem it solves.
        existing_materials: Optional - Any existing positioning, messaging, or marketing materials

    Returns:
        Structured analysis of the product with identified gaps
    """
    analysis = f"""
## Product Analysis

### Input Summary
{product_description[:500]}...

### Structured Extraction

**What I understand:**
- Product category and type
- Core problem being solved
- Key features mentioned
- Target audience indicators

**What I need to clarify:**
- Specific ICP definition (company size, role, industry)
- Quantified proof points (benchmarks, case studies)
- Competitive set and differentiation claims
- Current positioning (if any exists)
- Success metrics and goals

### Recommended Next Steps
1. Use `identify_icp` to define target customer precisely
2. Use `extract_value_props` to map features to benefits
3. Use `search_competitors` to understand competitive context

### Existing Materials Analysis
{f"Reviewed: {existing_materials[:200]}..." if existing_materials else "No existing materials provided - starting fresh."}
"""
    return analysis


@tool
def extract_value_props(
    features: str,
    target_audience: str,
    competitive_context: Optional[str] = None,
) -> str:
    """
    Extract value propositions by translating features into customer benefits.

    Use this tool to convert a list of product features into compelling
    value propositions that resonate with the target audience.

    Args:
        features: List of product features to analyze
        target_audience: Who the product is for
        competitive_context: How competitors position similar features

    Returns:
        Feature-to-benefit mapping with value propositions
    """
    return f"""
## Value Proposition Extraction

### Target Audience
{target_audience}

### Feature to Benefit Mapping

| Feature | Benefit (So What?) | Value Prop | Proof Point Needed |
|---------|-------------------|------------|-------------------|
| [Feature 1] | [Outcome for customer] | [Compelling statement] | [Evidence required] |
| [Feature 2] | [Outcome for customer] | [Compelling statement] | [Evidence required] |
| [Feature 3] | [Outcome for customer] | [Compelling statement] | [Evidence required] |

### Translation Framework Applied
- **Functional Value**: What does it do? (save time, reduce cost, increase output)
- **Emotional Value**: How does it feel? (confidence, peace of mind, pride)
- **Social Value**: What does it signal? (innovation, professionalism, leadership)

### Competitive Differentiation
{competitive_context if competitive_context else "No competitive context provided. Recommend using `search_competitors` to understand differentiation opportunities."}

### Strongest Value Props (Ranked)
1. [Highest impact, most differentiated]
2. [Strong supporting message]
3. [Tertiary message for specific segments]

### Gaps Identified
- Missing proof points for claims
- Unclear differentiation vs. alternatives
- Untested assumptions about customer priorities
"""


@tool
def identify_icp(
    product_description: str,
    current_customers: Optional[str] = None,
    excluded_segments: Optional[str] = None,
) -> str:
    """
    Define the Ideal Customer Profile (ICP) for positioning work.

    Use this tool to create a precise definition of who the product
    is for (and who it's NOT for).

    Args:
        product_description: What the product does
        current_customers: Description of existing customers if any
        excluded_segments: Segments to explicitly exclude

    Returns:
        Structured ICP definition with targeting criteria
    """
    default_excluded = "- Companies too small to need this\n- Teams without the pain point\n- Orgs with conflicting technology"
    excluded_text = excluded_segments if excluded_segments else default_excluded
    
    default_customers = "No current customer data provided. Consider customer interviews or survey data."
    customers_text = current_customers if current_customers else default_customers
    
    return f"""
## Ideal Customer Profile (ICP) Definition

### Primary ICP

**Company Characteristics:**
- Industry: [Specific verticals]
- Size: [Employee count / Revenue range]
- Stage: [Startup / Growth / Enterprise]
- Tech Stack: [Relevant technologies]
- Geography: [Regions/countries]

**Buyer Persona:**
- Title: [Decision maker role]
- Department: [Where they sit]
- Seniority: [Level in org]
- Reports to: [Who they answer to]
- KPIs: [What they're measured on]

**Situation Triggers:**
- [Event that creates urgency]
- [Pain point that's acute]
- [Change in circumstances]

### Anti-ICP (Who We're NOT For)
{excluded_text}

### Current Customer Signals
{customers_text}

### Validation Questions
1. Would they self-identify with this description?
2. Can we reach them through scalable channels?
3. Do they have budget authority?
4. Is the pain point urgent enough to act?

### Next Steps
- Validate ICP with customer interviews
- Cross-reference with closed-won deals
- Test messaging with this segment
"""
