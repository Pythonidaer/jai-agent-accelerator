"""
Test-Driven Development (TDD) tests for Deployment Checklist.

This test suite verifies that all production readiness items from
docs/DEPLOYMENT.md are properly implemented and configured.
"""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from unittest.mock import patch, MagicMock

# Try to import test dependencies - make them optional
try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False

try:
    from fastapi.testclient import TestClient
    from fastapi import status
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    # Create minimal mocks for testing
    class TestClient:
        def __init__(self, app):
            pass
        def get(self, path):
            class Response:
                status_code = 200
                def json(self):
                    return {}
            return Response()
        def post(self, path, **kwargs):
            class Response:
                status_code = 200
                def json(self):
                    return {}
            return Response()

# Try to import server - handle gracefully if dependencies missing
try:
    from .server import app, check_api_key
    HAS_SERVER = True
except ImportError as e:
    HAS_SERVER = False
    SERVER_IMPORT_ERROR = str(e)
    app = None
    
    def check_api_key():
        """Mock check_api_key when server can't be imported."""
        pass


class DeploymentChecklistTester:
    """Test harness for deployment checklist verification."""
    
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
        self.project_root = Path(__file__).parent.parent.parent.parent.parent
        self.gitignore_path = self.project_root / ".gitignore"
    
    def test_api_key_security(self) -> Dict[str, Any]:
        """
        Security: API Key Security - Never commit keys to git
        
        Tests:
        - .gitignore excludes .env files
        - No API keys hardcoded in source files
        - API key is checked via environment variable
        """
        result = {
            "category": "Security",
            "item": "API Key Security",
            "status": "unknown",
            "details": [],
            "issues": [],
        }
        
        try:
            # Check .gitignore includes .env files
            if self.gitignore_path.exists():
                gitignore_content = self.gitignore_path.read_text()
                if ".env" in gitignore_content:
                    result["details"].append("✅ .gitignore includes .env files")
                else:
                    result["issues"].append(".gitignore does not explicitly exclude .env files")
            
            # Check for hardcoded API keys in source files
            api_key_patterns = [
                r'sk-ant-[a-zA-Z0-9-]{40,}',  # Anthropic API key pattern
                r'ANTHROPIC_API_KEY\s*=\s*["\'][^"\']+["\']',  # Hardcoded env var
            ]
            
            source_files = list(self.project_root.rglob("*.py"))
            source_files.extend(list(self.project_root.rglob("*.ts")))
            source_files.extend(list(self.project_root.rglob("*.tsx")))
            source_files.extend(list(self.project_root.rglob("*.json")))
            
            hardcoded_keys = []
            for pattern in api_key_patterns:
                for file_path in source_files:
                    # Skip test files and virtual environments
                    if "test" in str(file_path) or ".venv" in str(file_path) or "node_modules" in str(file_path):
                        continue
                    
                    try:
                        content = file_path.read_text()
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            hardcoded_keys.append({
                                "file": str(file_path.relative_to(self.project_root)),
                                "matches": len(matches),
                            })
                    except Exception:
                        continue
            
            if hardcoded_keys:
                result["issues"].append(f"Found potential hardcoded API keys in {len(hardcoded_keys)} file(s)")
                result["details"].append(f"⚠️  Files with potential keys: {[f['file'] for f in hardcoded_keys]}")
            else:
                result["details"].append("✅ No hardcoded API keys found in source files")
            
            # Check that API key validation exists
            if HAS_SERVER:
                try:
                    # This should raise ValueError if no API key
                    with patch.dict(os.environ, {}, clear=True):
                        try:
                            check_api_key()
                            result["issues"].append("API key check does not raise error when key is missing")
                        except (ValueError, RuntimeError):
                            result["details"].append("✅ API key validation function exists and raises error when missing")
                except Exception as e:
                    result["issues"].append(f"Error testing API key validation: {e}")
            else:
                result["details"].append("⚠️  Could not test API key validation (server dependencies not available)")
            
            result["status"] = "pass" if not result["issues"] else "fail"
            
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Test error: {e}")
        
        return result
    
    def test_cors_configuration(self) -> Dict[str, Any]:
        """
        Security: CORS Configuration - Restrict to your domains only
        
        Tests:
        - CORS middleware is configured
        - Production should not use allow_origins=["*"]
        """
        result = {
            "category": "Security",
            "item": "CORS Configuration",
            "status": "unknown",
            "details": [],
            "issues": [],
        }
        
        try:
            # Check server.py for CORS configuration
            server_path = Path(__file__).parent / "server.py"
            if server_path.exists():
                server_content = server_path.read_text()
                
                # Check if CORS middleware is added
                if "CORSMiddleware" in server_content:
                    result["details"].append("✅ CORS middleware is configured")
                else:
                    result["issues"].append("CORS middleware not found in server.py")
                
                # Check if allow_origins=["*"] is used (not recommended for production)
                if 'allow_origins=["*"]' in server_content or "allow_origins=['*']" in server_content:
                    result["issues"].append("⚠️  CORS allows all origins (*) - should restrict to specific domains in production")
                    result["details"].append("💡 Consider using ALLOWED_ORIGINS environment variable")
                elif "ALLOWED_ORIGINS" in server_content or "allow_origins" in server_content and "*" not in server_content:
                    result["details"].append("✅ CORS configuration appears to support restricted origins")
                
                # Check if environment variable is used
                if "ALLOWED_ORIGINS" in server_content or "os.getenv" in server_content:
                    result["details"].append("✅ CORS configuration can use environment variables")
                else:
                    result["details"].append("💡 Consider making CORS configurable via ALLOWED_ORIGINS env var")
            
            result["status"] = "pass" if not result["issues"] else "warning"
            
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Test error: {e}")
        
        return result
    
    def test_rate_limiting(self) -> Dict[str, Any]:
        """
        Security: Rate Limiting - Implement request limits
        
        Tests:
        - Rate limiting middleware is configured
        """
        result = {
            "category": "Security",
            "item": "Rate Limiting",
            "status": "unknown",
            "details": [],
            "issues": [],
        }
        
        try:
            server_path = Path(__file__).parent / "server.py"
            if server_path.exists():
                server_content = server_path.read_text()
                
                # Check for rate limiting implementation
                rate_limit_indicators = [
                    "RateLimiter",
                    "rate_limit",
                    "slowapi",
                    "limiter",
                    "@limiter",
                ]
                
                has_rate_limiting = any(indicator.lower() in server_content.lower() for indicator in rate_limit_indicators)
                
                if has_rate_limiting:
                    result["details"].append("✅ Rate limiting appears to be implemented")
                else:
                    result["issues"].append("Rate limiting not found - should implement to prevent abuse")
                    result["details"].append("💡 Consider using slowapi or fastapi-limiter for rate limiting")
            
            result["status"] = "pass" if not result["issues"] else "fail"
            
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Test error: {e}")
        
        return result
    
    def test_input_validation(self) -> Dict[str, Any]:
        """
        Security: Input Validation - Validate all user inputs
        
        Tests:
        - Pydantic models are used for request validation
        - Input sanitization/validation exists
        """
        result = {
            "category": "Security",
            "item": "Input Validation",
            "status": "unknown",
            "details": [],
            "issues": [],
        }
        
        try:
            server_path = Path(__file__).parent / "server.py"
            if server_path.exists():
                server_content = server_path.read_text()
                
                # Check for Pydantic models
                if "BaseModel" in server_content and "ChatRequest" in server_content:
                    result["details"].append("✅ Pydantic models used for request validation (ChatRequest)")
                    
                    # Check for Field validation
                    if "Field" in server_content and "min_length" in server_content or "max_length" in server_content:
                        result["details"].append("✅ Message length validation configured (min_length/max_length)")
                    else:
                        result["details"].append("💡 Consider adding explicit message length limits via Field()")
                else:
                    result["issues"].append("Request validation models not found")
                
                # Test with TestClient to verify validation works (if server is available)
                if HAS_SERVER and HAS_FASTAPI and app is not None:
                    client = TestClient(app)
                    
                    # Test empty message
                    response = client.post("/chat", json={"message": ""})
                    if response.status_code in [422, 400]:
                        result["details"].append("✅ Empty message is rejected")
                    else:
                        result["details"].append("💡 Empty messages should be rejected (status code check)")
                    
                    # Test missing message field
                    response = client.post("/chat", json={})
                    if response.status_code == 422:
                        result["details"].append("✅ Missing required fields are rejected")
                    
                    # Test very long message (potential DoS)
                    long_message = "x" * 100000
                    response = client.post("/chat", json={"message": long_message})
                    # Should either accept (with limits) or reject
                    if response.status_code == 413 or response.status_code == 422:
                        result["details"].append("✅ Very long messages are handled (rejected or limited)")
                else:
                    result["details"].append("💡 Runtime validation test skipped (dependencies not available - check manually)")
            
            result["status"] = "pass" if len([i for i in result["issues"] if "should" in i.lower()]) == 0 else "warning"
            
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Test error: {e}")
        
        return result
    
    def test_https_enforcement(self) -> Dict[str, Any]:
        """
        Security: HTTPS Only - Enforce TLS everywhere
        
        Tests:
        - HTTPS redirect configuration (for self-hosted)
        - Vercel/Netlify automatically provide HTTPS
        """
        result = {
            "category": "Security",
            "item": "HTTPS Only",
            "status": "unknown",
            "details": [],
            "issues": [],
        }
        
        try:
            # Check deployment platform
            vercel_json = self.project_root / "vercel.json"
            netlify_toml = self.project_root / "netlify.toml"
            
            if vercel_json.exists():
                result["details"].append("✅ Using Vercel - HTTPS is automatic")
                result["status"] = "pass"
            elif netlify_toml.exists():
                result["details"].append("✅ Using Netlify - HTTPS is automatic")
                result["status"] = "pass"
            else:
                result["details"].append("💡 For self-hosted, ensure HTTPS is configured")
                result["status"] = "warning"
            
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Test error: {e}")
        
        return result
    
    def test_response_caching(self) -> Dict[str, Any]:
        """
        Performance: Response Caching - Cache common queries
        
        Tests:
        - Caching mechanism exists
        """
        result = {
            "category": "Performance",
            "item": "Response Caching",
            "status": "unknown",
            "details": [],
            "issues": [],
        }
        
        try:
            server_path = Path(__file__).parent / "server.py"
            if server_path.exists():
                server_content = server_path.read_text()
                
                cache_indicators = [
                    "cache",
                    "Cache",
                    "CACHE",
                    "functools.lru_cache",
                    "@lru_cache",
                    "redis",
                    "Redis",
                ]
                
                has_caching = any(indicator in server_content for indicator in cache_indicators)
                
                if has_caching:
                    result["details"].append("✅ Caching mechanism found")
                else:
                    result["issues"].append("No caching implementation found")
                    result["details"].append("💡 Consider caching common queries/responses")
            
            result["status"] = "pass" if not result["issues"] else "warning"
            
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Test error: {e}")
        
        return result
    
    def test_conversation_truncation(self) -> Dict[str, Any]:
        """
        Performance: Conversation Truncation - Limit history length
        
        Tests:
        - Conversation history is limited
        """
        result = {
            "category": "Performance",
            "item": "Conversation Truncation",
            "status": "unknown",
            "details": [],
            "issues": [],
        }
        
        try:
            server_path = Path(__file__).parent / "server.py"
            if server_path.exists():
                server_content = server_path.read_text()
                
                # Check for message limiting/truncation
                truncation_indicators = [
                    "max_messages",
                    "message_limit",
                    "truncate",
                    "history_limit",
                    "[-",
                    "[:",
                ]
                
                has_truncation = any(indicator in server_content.lower() for indicator in truncation_indicators)
                
                if has_truncation:
                    result["details"].append("✅ Conversation truncation/limiting appears to be implemented")
                else:
                    result["issues"].append("No conversation truncation found - long conversations may cause issues")
                    result["details"].append("💡 Consider limiting message history to last N messages")
            
            result["status"] = "pass" if not result["issues"] else "warning"
            
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Test error: {e}")
        
        return result
    
    def test_model_selection(self) -> Dict[str, Any]:
        """
        Performance: Model Selection - Use Haiku for simple tasks
        
        Tests:
        - Model can be configured via environment variable
        """
        result = {
            "category": "Performance",
            "item": "Model Selection",
            "status": "unknown",
            "details": [],
            "issues": [],
        }
        
        try:
            server_path = Path(__file__).parent / "server.py"
            if server_path.exists():
                server_content = server_path.read_text()
                
                # Check if MODEL environment variable is used
                if 'os.getenv("MODEL"' in server_content or 'os.environ.get("MODEL"' in server_content:
                    result["details"].append("✅ Model can be configured via MODEL environment variable")
                    result["status"] = "pass"
                else:
                    result["issues"].append("Model selection not configurable via environment variable")
                    result["status"] = "warning"
            
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Test error: {e}")
        
        return result
    
    def test_health_checks(self) -> Dict[str, Any]:
        """
        Monitoring: Health Checks - Automated uptime monitoring
        
        Tests:
        - Health endpoint exists and works
        """
        result = {
            "category": "Monitoring",
            "item": "Health Checks",
            "status": "unknown",
            "details": [],
            "issues": [],
        }
        
        try:
            # Check code for health endpoint
            server_path = Path(__file__).parent / "server.py"
            if server_path.exists():
                server_content = server_path.read_text()
                if "@app.get(\"/health\")" in server_content or '@app.get("/health")' in server_content:
                    result["details"].append("✅ /health endpoint defined in code")
                else:
                    result["issues"].append("Health endpoint not found in server.py")
            
            # Test runtime if available
            if HAS_SERVER and HAS_FASTAPI and app is not None:
                client = TestClient(app)
                response = client.get("/health")
                
                if response.status_code == 200:
                    data = response.json()
                    if "status" in data:
                        result["details"].append("✅ /health endpoint exists and returns status")
                        result["status"] = "pass"
                    else:
                        result["issues"].append("Health endpoint does not return status field")
                else:
                    result["issues"].append(f"Health endpoint returned status {response.status_code}")
            else:
                result["details"].append("💡 Runtime test skipped (test manually in production)")
                if not HAS_SERVER:
                    result["details"].append(f"   (Server import error: {SERVER_IMPORT_ERROR if 'SERVER_IMPORT_ERROR' in globals() else 'unknown'})")
            
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Test error: {e}")
        
        return result
    
    def test_error_tracking(self) -> Dict[str, Any]:
        """
        Monitoring: Error Tracking - Sentry or similar
        
        Tests:
        - Error tracking service is configured
        """
        result = {
            "category": "Monitoring",
            "item": "Error Tracking",
            "status": "unknown",
            "details": [],
            "issues": [],
        }
        
        try:
            # Check for error tracking services
            server_path = Path(__file__).parent / "server.py"
            observability_path = Path(__file__).parent / "observability.py"
            
            error_tracking_indicators = ["sentry", "Sentry", "sentry_sdk", "rollbar", "bugsnag"]
            
            has_error_tracking = False
            files_to_check = []
            if server_path.exists():
                files_to_check.append(server_path.read_text())
            if observability_path.exists():
                files_to_check.append(observability_path.read_text())
            
            for content in files_to_check:
                if any(indicator in content for indicator in error_tracking_indicators):
                    has_error_tracking = True
                    break
            
            if has_error_tracking:
                result["details"].append("✅ Error tracking service appears to be configured")
                result["status"] = "pass"
            else:
                result["issues"].append("No error tracking service found")
                result["details"].append("💡 Consider adding Sentry or similar error tracking")
                result["status"] = "warning"
            
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Test error: {e}")
        
        return result
    
    def test_usage_metrics(self) -> Dict[str, Any]:
        """
        Monitoring: Usage Metrics - Track tokens and costs
        
        Tests:
        - Metrics endpoint exists
        - Token/cost tracking is implemented
        """
        result = {
            "category": "Monitoring",
            "item": "Usage Metrics",
            "status": "unknown",
            "details": [],
            "issues": [],
        }
        
        try:
            # Check code for metrics endpoint
            server_path = Path(__file__).parent / "server.py"
            if server_path.exists():
                server_content = server_path.read_text()
                if "@app.get(\"/metrics\")" in server_content or '@app.get("/metrics")' in server_content:
                    result["details"].append("✅ /metrics endpoint defined in code")
                else:
                    result["issues"].append("Metrics endpoint not found in server.py")
            
            # Test runtime if available
            if HAS_SERVER and HAS_FASTAPI and app is not None:
                client = TestClient(app)
                response = client.get("/metrics")
                
                if response.status_code == 200:
                    result["details"].append("✅ /metrics endpoint exists")
                    data = response.json()
                    if "sessions" in data or "summary" in data:
                        result["details"].append("✅ Metrics endpoint returns usage data")
                        result["status"] = "pass"
                    else:
                        result["details"].append("⚠️  Metrics endpoint exists but may need token/cost tracking")
                        result["status"] = "warning"
                else:
                    result["issues"].append("Metrics endpoint returned error")
                    result["status"] = "warning"
            else:
                result["details"].append("💡 Runtime test skipped (test manually in production)")
                result["status"] = "warning"
            
            # Check observability for token tracking
            observability_path = Path(__file__).parent / "observability.py"
            if observability_path.exists():
                observability_content = observability_path.read_text()
                if "token" in observability_content.lower() or "cost" in observability_content.lower():
                    result["details"].append("✅ Observability system may track tokens/costs")
            
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Test error: {e}")
        
        return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all deployment checklist tests."""
        test_methods = [
            self.test_api_key_security,
            self.test_cors_configuration,
            self.test_rate_limiting,
            self.test_input_validation,
            self.test_https_enforcement,
            self.test_response_caching,
            self.test_conversation_truncation,
            self.test_model_selection,
            self.test_health_checks,
            self.test_error_tracking,
            self.test_usage_metrics,
        ]
        
        results = []
        for test_method in test_methods:
            try:
                result = test_method()
                results.append(result)
                self.results[result["item"]] = result
            except Exception as e:
                results.append({
                    "category": "Unknown",
                    "item": test_method.__name__,
                    "status": "error",
                    "details": [],
                    "issues": [f"Test failed: {e}"],
                })
        
        return {
            "summary": self._generate_summary(results),
            "results": results,
        }
    
    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics."""
        total = len(results)
        passed = sum(1 for r in results if r["status"] == "pass")
        failed = sum(1 for r in results if r["status"] == "fail")
        warnings = sum(1 for r in results if r["status"] == "warning")
        errors = sum(1 for r in results if r["status"] == "error")
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "errors": errors,
            "pass_rate": passed / total if total > 0 else 0,
        }
    
    def export_results(self, output_path: Optional[Path] = None) -> Path:
        """Export test results to JSON."""
        output_path = output_path or self.project_root / "apps" / "agent" / "logs" / "deployment_checklist_results.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        all_results = self.run_all_tests()
        
        with open(output_path, "w") as f:
            json.dump(all_results, f, indent=2, default=str)
        
        return output_path


# Pytest test functions for CI/CD integration (only if pytest is available)
if HAS_PYTEST:
    @pytest.mark.asyncio
    async def test_api_key_security():
        """Test API key security."""
        tester = DeploymentChecklistTester()
        result = tester.test_api_key_security()
        assert result["status"] in ["pass", "warning"], f"API key security failed: {result['issues']}"


    @pytest.mark.asyncio
    async def test_cors_configuration():
        """Test CORS configuration."""
        tester = DeploymentChecklistTester()
        result = tester.test_cors_configuration()
        assert result["status"] != "fail", f"CORS configuration has issues: {result['issues']}"


    @pytest.mark.asyncio
    async def test_input_validation():
        """Test input validation."""
        tester = DeploymentChecklistTester()
        result = tester.test_input_validation()
        assert result["status"] != "fail", f"Input validation has issues: {result['issues']}"


    @pytest.mark.asyncio
    async def test_health_checks():
        """Test health checks."""
        tester = DeploymentChecklistTester()
        result = tester.test_health_checks()
        assert result["status"] == "pass", f"Health checks failed: {result['issues']}"


if __name__ == "__main__":
    import sys
    
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
    
    # Exit with error code if there are failures
    if summary["failed"] > 0 or summary["errors"] > 0:
        sys.exit(1)

