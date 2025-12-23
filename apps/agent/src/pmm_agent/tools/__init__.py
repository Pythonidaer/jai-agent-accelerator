"""
PMM Agent Tools.

Tools are organized by workflow phase:
- INTAKE: Product analysis and requirements extraction
- RESEARCH: Competitive intelligence and market research
- PLANNING: Positioning, messaging, and launch planning
- RISK: Market risk assessment and validation
"""

from .intake import (
    analyze_product,
    extract_value_props,
    identify_icp,
)

from .research import (
    search_competitors,
    analyze_pricing,
    fetch_url,
    analyze_reviews,
)

from .planning import (
    create_positioning_statement,
    create_messaging_matrix,
    create_battlecard,
    create_launch_plan,
    create_checklist,
)

from .risk import (
    assess_market_risks,
    validate_positioning,
    identify_gaps,
)

from .scoring import (
    calculate_positioning_readiness,
)

# Tool categories for mode-based selection
INTAKE_TOOLS = [
    analyze_product,
    extract_value_props,
    identify_icp,
]

RESEARCH_TOOLS = [
    search_competitors,
    analyze_pricing,
    fetch_url,
    analyze_reviews,
]

PLANNING_TOOLS = [
    create_positioning_statement,
    create_messaging_matrix,
    create_battlecard,
    create_launch_plan,
    create_checklist,
]

RISK_TOOLS = [
    assess_market_risks,
    validate_positioning,
    identify_gaps,
]

SCORING_TOOLS = [
    calculate_positioning_readiness,
]

ALL_TOOLS = INTAKE_TOOLS + RESEARCH_TOOLS + PLANNING_TOOLS + RISK_TOOLS + SCORING_TOOLS

# Tools that require human approval before execution
HUMAN_APPROVAL_TOOLS = [
    "create_positioning_statement",
    "create_messaging_matrix",
    "create_launch_plan",
]
