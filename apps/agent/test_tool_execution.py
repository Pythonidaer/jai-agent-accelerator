#!/usr/bin/env python3
"""
Test tool execution to verify tools are working correctly.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from pmm_agent.tools.intake import analyze_product


async def test_analyze_product():
    """Test that analyze_product tool executes and returns results."""
    print("Testing analyze_product tool...")
    print("=" * 80)
    
    test_description = "Job seekers currently rely on spreadsheets, bookmarks, and guesswork to understand job market trends, and Job Trend Analyzer replaces that with structured, data-driven insight into roles and in-demand skills."
    
    try:
        # Test synchronous execution
        result = analyze_product.invoke({
            "product_description": test_description
        })
        
        print("✅ Tool executed successfully!")
        print("\nTool Result:")
        print("-" * 80)
        print(result)
        print("-" * 80)
        
        # Verify result has expected content
        assert "Product Analysis" in result, "Result should contain 'Product Analysis'"
        assert "What I understand" in result, "Result should contain 'What I understand'"
        assert "What I need to clarify" in result, "Result should contain 'What I need to clarify'"
        
        print("\n✅ All assertions passed!")
        print("\nTool is working correctly and returns structured analysis.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_analyze_product())
    sys.exit(0 if success else 1)

