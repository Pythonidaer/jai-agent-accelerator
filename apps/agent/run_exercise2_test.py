#!/usr/bin/env python3
"""
Quick test runner for Exercise 2.

Usage:
    python run_exercise2_test.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pmm_agent.test_exercise2 import Exercise2Tester


async def main():
    """Run Exercise 2 tests."""
    print("="*80)
    print("EXERCISE 2: PROMPT SURGERY - TEST SUITE")
    print("="*80)
    print("\nTesting Clarification Protocol behavior...\n")
    
    tester = Exercise2Tester()
    summary = await tester.run_test_suite(num_iterations=5)
    
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']} ✅")
    print(f"Failed: {summary['failed']} ❌")
    print(f"Pass Rate: {summary['pass_rate']*100:.1f}%")
    
    if summary['issues']:
        print("\nIssues Found:")
        for issue, count in summary['issues'].items():
            print(f"  [{count}x] {issue}")
    
    print("\nDetailed Results:")
    for i, result in enumerate(summary['results'], 1):
        status = "✅ PASS" if result['followed_protocol'] else "❌ FAIL"
        print(f"\n  Test {i}: {status}")
        print(f"    Message: {result['test_message']}")
        if result['clarification_question']:
            print(f"    Question: {result['clarification_question'][:80]}...")
        if result['tools_called']:
            print(f"    Tools Called: {', '.join(result['tools_called'])}")
        print(f"    Issue: {result['issue']}")
    
    # Export results
    output_path = tester.export_results()
    print(f"\n📊 Full results exported to: {output_path}")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())

