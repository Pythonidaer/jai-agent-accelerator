# Custom Tools Testing Guide

This document explains how to test your custom tools to verify they work correctly before deployment.

## Quick Start

```bash
cd apps/agent

# Activate your virtual environment (if you have one)
source .venv/bin/activate  # or: source venv/bin/activate

# Run the test suite
python3 tests/test_custom_tools.py
```

## What Gets Tested

The test suite verifies at least 3 custom tools (we test 4 for extra confidence):

1. ✅ **`calculate_positioning_readiness`** (scoring.py)
   - Tests structured output (Pydantic model)
   - Verifies scoring logic (0-10 scale)
   - Checks strengths/gaps identification

2. ✅ **`analyze_product`** (intake.py)
   - Tests product analysis functionality
   - Verifies structured output format
   - Checks content requirements

3. ✅ **`create_positioning_statement`** (planning.py)
   - Tests positioning statement creation
   - Verifies template formatting
   - Checks all required sections

4. ✅ **`extract_value_props`** (intake.py) - Bonus test
   - Tests value proposition extraction
   - Verifies feature-to-benefit mapping

## Test Output

The test script generates:

1. **Console output** - Real-time test results with pass/fail status
2. **JSON log file** - Detailed results saved to `logs/tool_test_YYYYMMDD_HHMMSS.json`

### Sample Output

```
================================================================================
TEST SUMMARY
================================================================================
Total Tools Tested: 4
✅ Passed: 4
❌ Failed: 0
Pass Rate: 100.0%

📄 Detailed logs saved to: logs/tool_test_20251224_112025.json

✅ REQUIREMENT MET - Ready for deployment!
```

## Log File Structure

The JSON log file contains:

```json
{
  "test_run_timestamp": "2025-12-24T11:20:25.540057",
  "total_tools_tested": 4,
  "passed": 4,
  "failed": 0,
  "pass_rate": 1.0,
  "test_results": [
    {
      "tool_name": "calculate_positioning_readiness",
      "timestamp": "2025-12-24T11:20:25.540123",
      "success": true,
      "result_type": "ReadinessScore",
      "result_preview": "...",
      "error": null
    },
    ...
  ]
}
```

## Requirements Verification

The test script automatically verifies that **at least 3 tools are working**. If this requirement is met, you'll see:

```
✅ REQUIREMENT MET - Ready for deployment!
```

If the requirement is not met:

```
❌ REQUIREMENT NOT MET - Need X more tools to pass
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'langchain_core'"

**Solution:** Activate your virtual environment and install dependencies:

```bash
cd apps/agent
source .venv/bin/activate  # or: source venv/bin/activate
pip install -e .
```

### "Tool execution failed"

**Solution:** 
1. Check the error message in the console output
2. Review the detailed error in the JSON log file
3. Verify the tool's code is correct in `src/pmm_agent/tools/`
4. Check that all required dependencies are installed

### "Assertion failed"

**Solution:**
1. Review which assertion failed
2. Check the tool's implementation
3. Verify the tool returns the expected data structure
4. Check the test expectations match the tool's actual behavior

## Adding More Tests

To test additional tools, add new test methods to the `ToolTester` class in `tests/test_custom_tools.py`:

```python
def test_your_new_tool(self) -> Dict[str, Any]:
    """Test your new tool."""
    tool_name = "your_new_tool"
    print(f"\n{'='*80}")
    print(f"Testing: {tool_name}")
    
    try:
        # Your test code here
        result = your_new_tool.invoke({...})
        
        # Verify result
        assert isinstance(result, expected_type), "Result should be ..."
        
        return self.log_test_result(tool_name, True, result)
    except Exception as e:
        return self.log_test_result(tool_name, False, None, str(e))
```

Then add the test to `run_all_tests()`:

```python
test5 = self.test_your_new_tool()
```

## Next Steps

After all tests pass:

1. ✅ Review the log file to verify detailed results
2. ✅ Commit the test script and logs to git
3. ✅ Proceed with deployment
4. ✅ Use the logs as evidence that tools are working

## Related Files

- **Test script**: `apps/agent/tests/test_custom_tools.py`
- **Log files**: `apps/agent/logs/tool_test_*.json`
- **Tool implementations**: `apps/agent/src/pmm_agent/tools/*.py`

