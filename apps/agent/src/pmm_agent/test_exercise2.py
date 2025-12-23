"""
Test suite for Exercise 2: Prompt Surgery.

Tests the Clarification Protocol behavior to identify issues.
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

from .prompts import MAIN_SYSTEM_PROMPT
from .tools import ALL_TOOLS
from .observability import get_logger, AgentLogger


class Exercise2Tester:
    """Test harness for Exercise 2."""
    
    def __init__(self):
        self.logger = get_logger()
        self.llm = ChatAnthropic(
            model_name="claude-sonnet-4-20250514",
            max_tokens=8192,
            system=MAIN_SYSTEM_PROMPT,
        )
        self.llm_with_tools = self.llm.bind_tools(ALL_TOOLS)
        self.results: List[Dict[str, Any]] = []
    
    async def test_clarification_protocol(
        self,
        test_message: str = "Help me position my SaaS product",
        session_id: str = "test_session",
    ) -> Dict[str, Any]:
        """
        Test if agent follows clarification protocol.
        
        Returns:
            Test result with analysis
        """
        self.logger.logger.info(f"[TEST] Testing clarification protocol with: '{test_message}'")
        
        messages = [HumanMessage(content=test_message)]
        tool_calls_detected = []
        response_text = ""
        start_time = asyncio.get_event_loop().time()
        
        # Stream the response and track tool calls
        async for chunk in self.llm_with_tools.astream(
            [{"role": "system", "content": MAIN_SYSTEM_PROMPT}] + messages
        ):
            # Track text content
            if hasattr(chunk, 'content') and chunk.content:
                content = chunk.content
                if isinstance(content, str):
                    response_text += content
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            response_text += item.get('text', '')
            
            # Track tool calls
            if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                for tc in chunk.tool_calls:
                    tool_calls_detected.append({
                        "name": tc.get('name'),
                        "args": tc.get('args', {}),
                    })
                    self.logger.log_tool_call(
                        tool_name=tc.get('name'),
                        args=tc.get('args', {}),
                        session_id=session_id,
                    )
        
        response_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        
        # Analyze result
        has_question = "?" in response_text
        called_tools = len(tool_calls_detected) > 0
        followed_protocol = has_question and not called_tools
        
        # Extract question if present
        clarification_question = None
        if has_question:
            lines = response_text.split("\n")
            questions = [line.strip() for line in lines if "?" in line and len(line.strip()) > 10]
            clarification_question = questions[0] if questions else None
        
        result = {
            "test_message": test_message,
            "session_id": session_id,
            "followed_protocol": followed_protocol,
            "has_question": has_question,
            "clarification_question": clarification_question,
            "called_tools": called_tools,
            "tools_called": [tc["name"] for tc in tool_calls_detected],
            "response_text": response_text,
            "response_time_ms": response_time_ms,
            "issue": self._identify_issue(followed_protocol, has_question, called_tools, tool_calls_detected),
        }
        
        self.results.append(result)
        self.logger.logger.info(f"[TEST RESULT] Protocol: {'✅ PASSED' if followed_protocol else '❌ FAILED'}")
        if not followed_protocol:
            self.logger.logger.warning(f"[TEST ISSUE] {result['issue']}")
        
        return result
    
    def _identify_issue(
        self,
        followed_protocol: bool,
        has_question: bool,
        called_tools: bool,
        tool_calls: List[Dict],
    ) -> str:
        """Identify the specific issue."""
        if followed_protocol:
            return "None - Protocol followed correctly"
        
        if called_tools and not has_question:
            return f"Agent called {len(tool_calls)} tools without asking a question first. Tools: {[tc['name'] for tc in tool_calls]}"
        
        if called_tools and has_question:
            return f"Agent asked a question but also called {len(tool_calls)} tools immediately. Should wait for answer first. Tools: {[tc['name'] for tc in tool_calls]}"
        
        if not has_question and not called_tools:
            return "Agent provided response without asking question or calling tools (might be follow-up response)"
        
        return "Unknown issue"
    
    async def run_test_suite(self, num_iterations: int = 3) -> Dict[str, Any]:
        """Run multiple test iterations to check consistency."""
        self.logger.logger.info(f"[TEST SUITE] Running {num_iterations} iterations")
        
        for i in range(num_iterations):
            session_id = f"test_session_{i}"
            await self.test_clarification_protocol(session_id=session_id)
            await asyncio.sleep(0.5)  # Small delay between tests
        
        # Analyze results
        passed = sum(1 for r in self.results if r["followed_protocol"])
        failed = len(self.results) - passed
        
        issues = {}
        for result in self.results:
            issue = result["issue"]
            if issue not in issues:
                issues[issue] = 0
            issues[issue] += 1
        
        summary = {
            "total_tests": len(self.results),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(self.results) if self.results else 0,
            "issues": issues,
            "results": self.results,
        }
        
        self.logger.logger.info(
            f"[TEST SUITE COMPLETE] Passed: {passed}/{len(self.results)} "
            f"({summary['pass_rate']*100:.1f}%)"
        )
        
        return summary
    
    def export_results(self, output_path: Optional[Path] = None) -> Path:
        """Export test results to JSON."""
        output_path = output_path or Path(__file__).parent.parent.parent / "logs" / "exercise2_test_results.json"
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        self.logger.logger.info(f"Test results exported to {output_path}")
        return output_path


async def main():
    """Run Exercise 2 tests."""
    tester = Exercise2Tester()
    summary = await tester.run_test_suite(num_iterations=5)
    
    print("\n" + "="*80)
    print("EXERCISE 2 TEST RESULTS")
    print("="*80)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Pass Rate: {summary['pass_rate']*100:.1f}%")
    print("\nIssues Found:")
    for issue, count in summary['issues'].items():
        print(f"  - {issue}: {count} occurrence(s)")
    print("="*80)
    
    tester.export_results()


if __name__ == "__main__":
    asyncio.run(main())

