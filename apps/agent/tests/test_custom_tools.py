#!/usr/bin/env python3
"""
Test Custom Tools - Verification Script for Tool Functionality

This script tests at least 3 custom tools to verify they work correctly
before deployment. Generates detailed logs for review.

Usage:
    # First, activate your virtual environment if you have one:
    # source .venv/bin/activate  # or source venv/bin/activate
    
    # Then install dependencies if needed:
    # pip install -e .
    
    # Run the tests:
    python3 tests/test_custom_tools.py
"""

import sys
import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import tools directly to avoid dependency issues
import importlib.util

def import_tool_module(module_name):
    """Import a tool module directly without going through __init__.py"""
    module_path = src_path / "pmm_agent" / "tools" / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import tool modules directly
scoring_module = import_tool_module("scoring")
intake_module = import_tool_module("intake")
planning_module = import_tool_module("planning")

# Get the tools
calculate_positioning_readiness = scoring_module.calculate_positioning_readiness
analyze_product = intake_module.analyze_product
extract_value_props = intake_module.extract_value_props
create_positioning_statement = planning_module.create_positioning_statement


class ToolTester:
    """Test harness for custom tools."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.log_file = Path(__file__).parent / "logs" / f"tool_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_test_result(self, tool_name: str, success: bool, result: Any, error: str = None):
        """Log test result."""
        test_result = {
            "tool_name": tool_name,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "result_preview": str(result)[:500] if result else None,
            "result_type": type(result).__name__ if result else None,
            "error": error,
        }
        self.results.append(test_result)
        return test_result
    
    def test_calculate_positioning_readiness(self) -> Dict[str, Any]:
        """Test the positioning readiness scoring tool."""
        tool_name = "calculate_positioning_readiness"
        print(f"\n{'='*80}")
        print(f"Testing: {tool_name}")
        print(f"{'='*80}")
        
        try:
            # Test case 1: Partially ready product
            print("\n📋 Test Case 1: Partially ready product")
            print("-" * 80)
            args = {
                "has_target_customer": True,
                "has_competitive_alternative": True,
                "has_key_differentiator": True,
                "has_customer_proof": False,
                "has_clear_category": False,
            }
            print(f"Input: {json.dumps(args, indent=2)}")
            
            result = calculate_positioning_readiness.invoke(args)
            print(f"\n✅ Tool executed successfully!")
            print(f"Result type: {type(result)}")
            
            # Check if result is a Pydantic model
            if hasattr(result, 'score'):
                print(f"Score: {result.score}/10")
                print(f"Strengths: {result.strengths}")
                print(f"Gaps: {result.gaps}")
                print(f"Next Action: {result.next_action}")
                
                # Verify expected output
                assert isinstance(result.score, int), "Score should be an integer"
                assert 0 <= result.score <= 10, "Score should be between 0-10"
                assert isinstance(result.strengths, list), "Strengths should be a list"
                assert isinstance(result.gaps, list), "Gaps should be a list"
                assert len(result.strengths) == 3, f"Expected 3 strengths, got {len(result.strengths)}"
                assert len(result.gaps) == 2, f"Expected 2 gaps, got {len(result.gaps)}"
                print("\n✅ All assertions passed!")
                
                return self.log_test_result(tool_name, True, result)
            else:
                error = f"Unexpected result type: {type(result)}. Expected Pydantic model with 'score' attribute."
                print(f"\n❌ {error}")
                return self.log_test_result(tool_name, False, result, error)
                
        except Exception as e:
            error = f"{type(e).__name__}: {str(e)}"
            print(f"\n❌ Error: {error}")
            traceback.print_exc()
            return self.log_test_result(tool_name, False, None, error)
    
    def test_analyze_product(self) -> Dict[str, Any]:
        """Test the product analysis tool."""
        tool_name = "analyze_product"
        print(f"\n{'='*80}")
        print(f"Testing: {tool_name}")
        print(f"{'='*80}")
        
        try:
            # Test case: Realistic product description
            print("\n📋 Test Case: Product analysis")
            print("-" * 80)
            product_description = (
                "Job Trend Analyzer is a SaaS platform that helps job seekers understand "
                "market trends and in-demand skills. It replaces spreadsheets and bookmarks "
                "with data-driven insights about roles, skills, and salary trends."
            )
            args = {
                "product_description": product_description,
                "existing_materials": None,
            }
            print(f"Input: {product_description[:100]}...")
            
            result = analyze_product.invoke(args)
            print(f"\n✅ Tool executed successfully!")
            print(f"Result type: {type(result)}")
            print(f"Result length: {len(result)} characters")
            print(f"\nResult preview (first 300 chars):")
            print("-" * 80)
            print(result[:300])
            print("-" * 80)
            
            # Verify expected content
            assert isinstance(result, str), "Result should be a string"
            assert len(result) > 100, "Result should be substantial"
            assert "Product Analysis" in result, "Result should contain 'Product Analysis'"
            assert "What I understand" in result, "Result should contain 'What I understand'"
            assert "What I need to clarify" in result, "Result should contain 'What I need to clarify'"
            print("\n✅ All assertions passed!")
            
            return self.log_test_result(tool_name, True, result)
            
        except Exception as e:
            error = f"{type(e).__name__}: {str(e)}"
            print(f"\n❌ Error: {error}")
            traceback.print_exc()
            return self.log_test_result(tool_name, False, None, error)
    
    def test_create_positioning_statement(self) -> Dict[str, Any]:
        """Test the positioning statement creation tool."""
        tool_name = "create_positioning_statement"
        print(f"\n{'='*80}")
        print(f"Testing: {tool_name}")
        print(f"{'='*80}")
        
        try:
            # Test case: Realistic positioning inputs
            print("\n📋 Test Case: Create positioning statement")
            print("-" * 80)
            args = {
                "target_customer": "Product managers at mid-size SaaS companies",
                "problem": "struggle to understand customer needs and prioritize features",
                "product_name": "Customer Insight Platform",
                "category": "customer intelligence platform",
                "key_benefit": "provides real-time customer feedback analysis and prioritization",
                "competitive_alternative": "spreadsheets and ad-hoc customer interviews",
                "differentiator": "automates analysis and provides AI-powered insights",
            }
            print(f"Input parameters:")
            for key, value in args.items():
                print(f"  {key}: {value[:60]}{'...' if len(value) > 60 else ''}")
            
            result = create_positioning_statement.invoke(args)
            print(f"\n✅ Tool executed successfully!")
            print(f"Result type: {type(result)}")
            print(f"Result length: {len(result)} characters")
            print(f"\nResult preview (first 400 chars):")
            print("-" * 80)
            print(result[:400])
            print("-" * 80)
            
            # Verify expected content
            assert isinstance(result, str), "Result should be a string"
            assert len(result) > 200, "Result should be substantial"
            assert "Positioning Statement" in result, "Result should contain 'Positioning Statement'"
            assert args["product_name"] in result, f"Result should contain product name: {args['product_name']}"
            assert args["target_customer"] in result or args["target_customer"].split()[0] in result, \
                f"Result should reference target customer"
            print("\n✅ All assertions passed!")
            
            return self.log_test_result(tool_name, True, result)
            
        except Exception as e:
            error = f"{type(e).__name__}: {str(e)}"
            print(f"\n❌ Error: {error}")
            traceback.print_exc()
            return self.log_test_result(tool_name, False, None, error)
    
    def test_extract_value_props(self) -> Dict[str, Any]:
        """Test the value proposition extraction tool (bonus 4th tool)."""
        tool_name = "extract_value_props"
        print(f"\n{'='*80}")
        print(f"Testing: {tool_name}")
        print(f"{'='*80}")
        
        try:
            # Test case: Feature to benefit mapping
            print("\n📋 Test Case: Extract value propositions")
            print("-" * 80)
            args = {
                "features": "Real-time analytics, Automated reporting, Custom dashboards, API access",
                "target_audience": "Product managers and data analysts",
                "competitive_context": "Competitors focus on batch processing and manual exports",
            }
            print(f"Input:")
            for key, value in args.items():
                print(f"  {key}: {value}")
            
            result = extract_value_props.invoke(args)
            print(f"\n✅ Tool executed successfully!")
            print(f"Result type: {type(result)}")
            print(f"Result length: {len(result)} characters")
            print(f"\nResult preview (first 300 chars):")
            print("-" * 80)
            print(result[:300])
            print("-" * 80)
            
            # Verify expected content
            assert isinstance(result, str), "Result should be a string"
            assert len(result) > 100, "Result should be substantial"
            assert "Value Proposition" in result, "Result should contain 'Value Proposition'"
            assert "features" in result.lower() or "benefit" in result.lower(), \
                "Result should discuss features or benefits"
            print("\n✅ All assertions passed!")
            
            return self.log_test_result(tool_name, True, result)
            
        except Exception as e:
            error = f"{type(e).__name__}: {str(e)}"
            print(f"\n❌ Error: {error}")
            traceback.print_exc()
            return self.log_test_result(tool_name, False, None, error)
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tool tests."""
        print("="*80)
        print("CUSTOM TOOLS TEST SUITE")
        print("="*80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Testing at least 3 custom tools for functionality verification")
        
        # Run tests
        test1 = self.test_calculate_positioning_readiness()
        test2 = self.test_analyze_product()
        test3 = self.test_create_positioning_statement()
        test4 = self.test_extract_value_props()  # Bonus 4th test
        
        # Generate summary
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        
        summary = {
            "test_run_timestamp": datetime.now().isoformat(),
            "total_tools_tested": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "pass_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "test_results": self.results,
        }
        
        # Save to file
        with open(self.log_file, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tools Tested: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Pass Rate: {summary['pass_rate']*100:.1f}%")
        print(f"\n📄 Detailed logs saved to: {self.log_file}")
        
        # Print detailed results
        print("\n" + "="*80)
        print("DETAILED RESULTS")
        print("="*80)
        for result in self.results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"\n{status} - {result['tool_name']}")
            if result["error"]:
                print(f"   Error: {result['error']}")
            else:
                print(f"   Result type: {result['result_type']}")
                if result["result_preview"]:
                    preview = result["result_preview"][:100] + "..." if len(result["result_preview"]) > 100 else result["result_preview"]
                    print(f"   Preview: {preview}")
        
        return summary
    
    def verify_minimum_requirements(self) -> bool:
        """Verify at least 3 tools passed."""
        passed_count = sum(1 for r in self.results if r["success"])
        meets_requirement = passed_count >= 3
        
        print("\n" + "="*80)
        print("REQUIREMENT VERIFICATION")
        print("="*80)
        print(f"Required: At least 3 tools working")
        print(f"Actual: {passed_count} tools passed")
        if meets_requirement:
            print("✅ REQUIREMENT MET - Ready for deployment!")
        else:
            print(f"❌ REQUIREMENT NOT MET - Need {3 - passed_count} more tools to pass")
        
        return meets_requirement


if __name__ == "__main__":
    tester = ToolTester()
    summary = tester.run_all_tests()
    meets_requirements = tester.verify_minimum_requirements()
    
    # Exit with appropriate code
    exit_code = 0 if meets_requirements else 1
    sys.exit(exit_code)

