#!/usr/bin/env python3
"""
Simple runner script for deployment checklist tests.

Usage:
    python3 tests/run_deployment_checklist_test.py
    
Note: This can be run without activating venv, as it only checks configuration
and code structure. Runtime tests are skipped if dependencies aren't available.
"""

import sys
import importlib.util
from pathlib import Path

# Import the test module directly without going through __init__.py
# This avoids importing heavy dependencies like langchain_anthropic
test_file_path = Path(__file__).parent.parent / "src" / "pmm_agent" / "test_deployment_checklist.py"
spec = importlib.util.spec_from_file_location("test_deployment_checklist", test_file_path)
test_module = importlib.util.module_from_spec(spec)

# Load the test module (it handles missing dependencies gracefully)
spec.loader.exec_module(test_module)

DeploymentChecklistTester = test_module.DeploymentChecklistTester

if __name__ == "__main__":
    tester = DeploymentChecklistTester()
    all_results = tester.run_all_tests()
    
    print("\n" + "="*80)
    print("DEPLOYMENT CHECKLIST TEST RESULTS")
    print("="*80)
    
    summary = all_results["summary"]
    print(f"\nSummary:")
    print(f"  Total Tests: {summary['total']}")
    print(f"  ✅ Passed: {summary['passed']}")
    print(f"  ❌ Failed: {summary['failed']}")
    print(f"  ⚠️  Warnings: {summary['warnings']}")
    print(f"  🔴 Errors: {summary['errors']}")
    print(f"  Pass Rate: {summary['pass_rate']*100:.1f}%")
    
    print("\n" + "="*80)
    print("DETAILED RESULTS")
    print("="*80)
    
    for result in all_results["results"]:
        status_icon = {
            "pass": "✅",
            "fail": "❌",
            "warning": "⚠️ ",
            "error": "🔴",
        }.get(result["status"], "❓")
        
        print(f"\n{status_icon} {result['category']}: {result['item']}")
        if result["details"]:
            for detail in result["details"]:
                print(f"   {detail}")
        if result["issues"]:
            for issue in result["issues"]:
                print(f"   ❌ {issue}")
    
    # Export results
    output_path = tester.export_results()
    print(f"\n\nResults exported to: {output_path}")
    print(f"\n📖 For manual verification steps, see: docs/DEPLOYMENT_CHECKLIST_VERIFICATION.md")
    
    # Exit with error code if there are failures
    exit_code = 0
    if summary["failed"] > 0 or summary["errors"] > 0:
        exit_code = 1
        print(f"\n❌ Some tests failed. Please review and fix issues.")
    elif summary["warnings"] > 0:
        print(f"\n⚠️  Some tests have warnings. Review recommendations.")
    
    sys.exit(exit_code)

