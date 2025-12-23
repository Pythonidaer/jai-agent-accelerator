"""
Observability and Logging for PMM Agent.

Tracks agent behavior, tool usage, and response quality for debugging and improvement.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class LogLevel(Enum):
    """Log severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class ToolCallEvent:
    """Record of a tool call."""
    tool_name: str
    args: Dict[str, Any]
    timestamp: float
    session_id: str
    message_id: Optional[str] = None
    duration_ms: Optional[float] = None
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class AgentResponseEvent:
    """Record of an agent response."""
    session_id: str
    message_id: str
    user_message: str
    agent_response: str
    timestamp: float
    tool_calls: List[ToolCallEvent]
    response_time_ms: float
    token_count: Optional[int] = None
    followed_clarification_protocol: Optional[bool] = None
    clarification_question: Optional[str] = None


@dataclass
class SessionMetrics:
    """Metrics for a conversation session."""
    session_id: str
    start_time: float
    message_count: int
    tool_call_count: int
    total_response_time_ms: float
    tools_used: List[str]
    errors: List[str]


class AgentLogger:
    """Centralized logging for agent observability."""
    
    def __init__(self, log_dir: Optional[Path] = None, enable_file_logging: bool = True):
        """
        Initialize logger.
        
        Args:
            log_dir: Directory to save log files (default: ./logs)
            enable_file_logging: Whether to write logs to files
        """
        self.log_dir = log_dir or Path(__file__).parent.parent.parent / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.enable_file_logging = enable_file_logging
        
        # Setup Python logging
        self.logger = logging.getLogger("pmm_agent")
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        if self.enable_file_logging:
            file_handler = logging.FileHandler(self.log_dir / "agent.log")
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        
        # Event storage
        self.events: List[AgentResponseEvent] = []
        self.sessions: Dict[str, SessionMetrics] = {}
    
    def log_tool_call(
        self,
        tool_name: str,
        args: Dict[str, Any],
        session_id: str,
        message_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """Log a tool call event."""
        event = ToolCallEvent(
            tool_name=tool_name,
            args=args,
            timestamp=time.time(),
            session_id=session_id,
            message_id=message_id,
            duration_ms=duration_ms,
            result=result,
            error=error,
        )
        
        self.logger.info(
            f"[TOOL] {tool_name} | Session: {session_id[:8]}... | "
            f"Args: {json.dumps(args, default=str)[:100]}"
        )
        
        if error:
            self.logger.error(f"[TOOL ERROR] {tool_name}: {error}")
        
        return event
    
    def log_response(
        self,
        session_id: str,
        message_id: str,
        user_message: str,
        agent_response: str,
        tool_calls: List[ToolCallEvent],
        response_time_ms: float,
        token_count: Optional[int] = None,
        is_first_message: bool = False,
    ):
        """Log an agent response event."""
        # Analyze if clarification protocol was followed (only check on first message)
        followed_protocol, clarification_q = self._analyze_clarification_protocol(
            user_message, agent_response, tool_calls, is_first_message
        )
        
        event = AgentResponseEvent(
            session_id=session_id,
            message_id=message_id,
            user_message=user_message,
            agent_response=agent_response,
            timestamp=time.time(),
            tool_calls=tool_calls,
            response_time_ms=response_time_ms,
            token_count=token_count,
            followed_clarification_protocol=followed_protocol,
            clarification_question=clarification_q,
        )
        
        self.events.append(event)
        
        # Update session metrics
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionMetrics(
                session_id=session_id,
                start_time=time.time(),
                message_count=0,
                tool_call_count=0,
                total_response_time_ms=0,
                tools_used=[],
                errors=[],
            )
        
        session = self.sessions[session_id]
        session.message_count += 1
        session.tool_call_count += len(tool_calls)
        session.total_response_time_ms += response_time_ms
        session.tools_used.extend([tc.tool_name for tc in tool_calls])
        
        # Log summary
        protocol_status = "✅ FOLLOWED" if followed_protocol else "❌ VIOLATED"
        self.logger.info(
            f"[RESPONSE] Session: {session_id[:8]}... | "
            f"Protocol: {protocol_status} | "
            f"Tools: {len(tool_calls)} | "
            f"Time: {response_time_ms:.0f}ms"
        )
        
        if not followed_protocol and len(tool_calls) > 0:
            self.logger.warning(
                f"[PROTOCOL VIOLATION] Agent called {len(tool_calls)} tools before asking clarifying question. "
                f"Tools: {[tc.tool_name for tc in tool_calls]}"
            )
        
        # Save to file
        if self.enable_file_logging:
            self._save_event(event)
        
        return event
    
    def _analyze_clarification_protocol(
        self,
        user_message: str,
        agent_response: str,
        tool_calls: List[ToolCallEvent],
        is_first_message: bool = False,
    ) -> tuple[Optional[bool], Optional[str]]:
        """
        Analyze if the agent followed the clarification protocol.
        
        The protocol only applies to the FIRST message in a conversation.
        After the user answers the clarifying question, the agent should proceed with analysis.
        
        Returns:
            (followed_protocol, clarification_question)
        """
        # Protocol only applies to first message
        if not is_first_message:
            return None, None  # Not applicable to follow-up messages
        
        # If tools were called immediately on first message, protocol was violated
        if len(tool_calls) > 0:
            # Check if response contains a question mark (might have asked AND called tools)
            has_question = "?" in agent_response
            if has_question:
                # Extract question if present
                lines = agent_response.split("\n")
                questions = [line for line in lines if "?" in line]
                clarification_q = questions[0] if questions else None
                # If it asked a question but also called tools, it's a violation
                return False, clarification_q
            return False, None
        
        # No tools called - check if it asked a question
        has_question = "?" in agent_response
        if has_question:
            lines = agent_response.split("\n")
            questions = [line for line in lines if "?" in line and len(line.strip()) > 10]
            clarification_q = questions[0] if questions else None
            return True, clarification_q
        
        # No question, no tools - might be a follow-up response
        return None, None
    
    def _save_event(self, event: AgentResponseEvent):
        """Save event to JSON file for analysis."""
        event_file = self.log_dir / f"events_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(event_file, "a") as f:
            f.write(json.dumps(asdict(event), default=str) + "\n")
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get summary metrics for a session."""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        events = [e for e in self.events if e.session_id == session_id]
        
        protocol_violations = sum(
            1 for e in events 
            if e.followed_clarification_protocol is False
        )
        
        return {
            "session_id": session_id,
            "message_count": session.message_count,
            "tool_call_count": session.tool_call_count,
            "total_response_time_ms": session.total_response_time_ms,
            "avg_response_time_ms": session.total_response_time_ms / session.message_count if session.message_count > 0 else 0,
            "tools_used": list(set(session.tools_used)),
            "protocol_violations": protocol_violations,
            "errors": session.errors,
        }
    
    def export_metrics(self, output_path: Optional[Path] = None) -> Path:
        """Export all metrics to JSON file."""
        output_path = output_path or self.log_dir / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        metrics = {
            "sessions": {
                sid: asdict(session) 
                for sid, session in self.sessions.items()
            },
            "events": [asdict(event) for event in self.events],
            "summary": {
                "total_sessions": len(self.sessions),
                "total_events": len(self.events),
                "total_tool_calls": sum(len(e.tool_calls) for e in self.events),
                "protocol_violations": sum(
                    1 for e in self.events 
                    if e.followed_clarification_protocol is False
                ),
            }
        }
        
        with open(output_path, "w") as f:
            json.dump(metrics, f, indent=2, default=str)
        
        self.logger.info(f"Metrics exported to {output_path}")
        return output_path


# Global logger instance
_logger_instance: Optional[AgentLogger] = None


def get_logger() -> AgentLogger:
    """Get or create the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AgentLogger()
    return _logger_instance

