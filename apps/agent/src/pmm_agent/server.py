"""
Simple FastAPI server for PMM Deep Agent.
Runs without Docker or LangSmith.
"""

import os
import json
import uuid
import time
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableLambda

from .prompts import MAIN_SYSTEM_PROMPT
from .tools import ALL_TOOLS
from .observability import get_logger
from .agent import create_pmm_agent

# Create a tool lookup for execution
TOOL_MAP = {tool.name: tool for tool in ALL_TOOLS}

# Initialize the ReAct agent - this enforces tool usage
agent = create_pmm_agent(mode="full", model_name=os.getenv("MODEL", "claude-sonnet-4-20250514"))

# Configure root_path for Vercel deployment
# Vercel passes /api/* paths, so FastAPI needs to know it's mounted at /api
import os
root_path = "/api" if os.getenv("VERCEL") else ""
app = FastAPI(title="PMM Deep Agent", version="0.1.0", root_path=root_path)

# CORS configuration - restrict origins in production
def get_allowed_origins():
    """Get allowed CORS origins based on environment."""
    # Check for explicit configuration
    allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
    if allowed_origins_env:
        # Split comma-separated list and strip whitespace
        return [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
    
    # Production environments should restrict origins
    is_production = os.getenv("VERCEL") or os.getenv("PRODUCTION") == "true" or os.getenv("ENVIRONMENT") == "production"
    
    if is_production:
        # In production, default to empty list (no CORS) unless explicitly configured
        # This ensures security - must set ALLOWED_ORIGINS explicitly
        return []
    else:
        # Development: allow all origins
        return ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Check for API key (only raise at runtime, not during import)
# This allows the function to be deployed even if env var isn't set during build
def check_api_key():
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Please set it before starting the server:\n"
            "  export ANTHROPIC_API_KEY=sk-ant-your-key-here"
        )

# Check on startup (FastAPI startup event)
@app.on_event("startup")
async def startup_check():
    check_api_key()

# Note: Agent is initialized above using create_pmm_agent which sets up ReAct loop
# This replaces the old llm_with_tools approach that didn't enforce tool usage

# Simple in-memory session storage
sessions: dict = {}

# Initialize observability
logger = get_logger()

# Configuration
MAX_MESSAGE_HISTORY = int(os.getenv("MAX_MESSAGE_HISTORY", "100"))  # Keep last 100 messages per session


def truncate_session_messages(session_messages: list) -> list:
    """
    Truncate session messages to prevent excessive token usage.
    Always keeps the system message and the most recent N messages.
    """
    if len(session_messages) <= MAX_MESSAGE_HISTORY + 1:  # +1 for system message
        return session_messages
    
    # Keep system message (first) + last MAX_MESSAGE_HISTORY messages
    system_message = session_messages[0] if session_messages and session_messages[0].get("role") == "system" else None
    recent_messages = session_messages[-(MAX_MESSAGE_HISTORY):] if system_message else session_messages[-MAX_MESSAGE_HISTORY:]
    
    if system_message:
        return [system_message] + recent_messages
    return recent_messages


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=50000, description="User message (1-50000 characters)")
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    tool_calls: list | None = None


@app.get("/health")
def health():
    return {"status": "ok", "agent": "jai-agent-accelerator", "version": "0.1.0"}


@app.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """Simple chat endpoint."""
    session_id = request.session_id or str(uuid.uuid4())

    # Get or create session
    if session_id not in sessions:
        sessions[session_id] = {
            "messages": [
                {"role": "system", "content": MAIN_SYSTEM_PROMPT}
            ]
        }

    session = sessions[session_id]
    session["messages"].append({"role": "user", "content": request.message})
    
    # Truncate messages to prevent excessive token usage
    session["messages"] = truncate_session_messages(session["messages"])

    # Convert to LangChain message format and use the agent
    langchain_messages = []
    for m in session["messages"]:
        if m["role"] == "system":
            continue  # System prompt handled by agent
        elif m["role"] == "user":
            langchain_messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            langchain_messages.append(AIMessage(content=m["content"]))
    
    # Use the ReAct agent - it will handle tool calling automatically
    config = {"configurable": {"thread_id": session_id}}
    result = await agent.ainvoke({"messages": langchain_messages}, config)
    
    # Extract final response from agent result
    # The agent returns messages list, get the last AI message
    response_text = ""
    tool_calls = []
    
    if isinstance(result, dict) and "messages" in result:
        messages_list = result["messages"]
        for msg in reversed(messages_list):
            if isinstance(msg, AIMessage):
                if isinstance(msg.content, str):
                    response_text = msg.content
                elif isinstance(msg.content, list):
                    for item in msg.content:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            response_text += item.get('text', '')
                
                # Extract tool calls if any
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_calls = [
                        {"name": tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', None),
                         "args": tc.get('args') or tc.get('input', {}) if isinstance(tc, dict) else getattr(tc, 'args', {})}
                        for tc in msg.tool_calls
                    ]
                break
    
    # Fallback if no response found
    if not response_text:
        response_text = "I processed your request. (Response extraction may need adjustment)"
    
    session["messages"].append({"role": "assistant", "content": response_text})

    return ChatResponse(
        session_id=session_id,
        response=response_text,
        tool_calls=tool_calls
    )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint."""
    session_id = request.session_id or str(uuid.uuid4())

    if session_id not in sessions:
        sessions[session_id] = {
            "messages": [
                {"role": "system", "content": MAIN_SYSTEM_PROMPT}
            ]
        }

    session = sessions[session_id]
    
    # Check if this is the first user message (for protocol tracking)
    user_messages = [m for m in session["messages"] if m["role"] == "user"]
    is_first_message = len(user_messages) == 0
    
    session["messages"].append({"role": "user", "content": request.message})
    
    # Truncate messages to prevent excessive token usage
    session["messages"] = truncate_session_messages(session["messages"])

    # Generate unique message ID for tracking
    message_id = str(uuid.uuid4())
    start_time = time.time()  # Initialize at function start
    tool_calls_tracked = []

    async def generate() -> AsyncGenerator[str, None]:
        # Convert session messages to LangChain message format
        # The agent expects messages in LangChain format (HumanMessage, AIMessage, etc.)
        langchain_messages = []
        for m in session["messages"]:
            if m["role"] == "system":
                continue  # System prompt is handled by agent
            elif m["role"] == "user":
                langchain_messages.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant":
                langchain_messages.append(AIMessage(content=m["content"]))
        
        full_response = ""
        
        # Track seen tool calls to prevent duplicates
        # Use (tool_name, args_hash) as key since tool calls might not have IDs
        seen_tool_calls = set()
        
        def get_tool_call_key(tool_name: str, tool_args: dict) -> str:
            """Generate a unique key for a tool call to detect duplicates."""
            try:
                args_str = json.dumps(tool_args, sort_keys=True)
            except (TypeError, ValueError):
                args_str = str(tool_args)
            return f"{tool_name}:{args_str}"
        
        # Debug logging
        is_local = not os.getenv("VERCEL") and not os.getenv("PRODUCTION")
        if is_local:
            print(f"\n🚀 [STREAM] Starting agent stream with {len(langchain_messages)} messages")
        
        try:
            # Use the ReAct agent's streaming - it handles tool calling internally
            # LangGraph streams events as {node_name: output} dictionaries
            async for event in agent.astream(
                {"messages": langchain_messages},
                {"configurable": {"thread_id": session_id}},
            ):
                if is_local:
                    print(f"📦 [STREAM] Event received: {list(event.keys())}")
                
                # LangGraph agent streams events with node names
                # Common node names: "agent" (AI thinking/calling), "tools" (tool execution)
                for node_name, node_output in event.items():
                    if is_local:
                        print(f"   Node: {node_name}, Type: {type(node_output).__name__}")
                    
                    # "agent" node contains AIMessage with text and/or tool_calls
                    # Note: LangGraph may return dict format with "messages" key
                    if node_name == "agent":
                        # Handle both dict and AIMessage formats
                        agent_message = None
                        if isinstance(node_output, dict):
                            # LangGraph returns {"messages": [AIMessage, ...]}
                            if "messages" in node_output and node_output["messages"]:
                                if is_local:
                                    print(f"   Dict has {len(node_output['messages'])} messages")
                                # Get the last message (usually the AI response)
                                for msg in reversed(node_output["messages"]):
                                    if isinstance(msg, AIMessage):
                                        agent_message = msg
                                        break
                        elif isinstance(node_output, AIMessage):
                            agent_message = node_output
                        
                        if is_local and agent_message is None:
                            print(f"   ⚠️  No AIMessage found in agent node output")
                        
                        if agent_message:
                            if is_local:
                                print(f"   Processing AIMessage, content type: {type(agent_message.content).__name__}")
                            
                            # Check for tool calls first
                            if hasattr(agent_message, 'tool_calls') and agent_message.tool_calls:
                                for tc in agent_message.tool_calls:
                                    # Handle both dict and object formats
                                    if isinstance(tc, dict):
                                        tool_name = tc.get('name')
                                        tool_args = tc.get('input') or tc.get('args', {})
                                    else:
                                        tool_name = getattr(tc, 'name', None)
                                        tool_args = getattr(tc, 'args', {}) or getattr(tc, 'input', {})
                                    
                                    if tool_name:
                                        # Check if we've already seen this tool call
                                        tool_call_key = get_tool_call_key(tool_name, tool_args)
                                        if tool_call_key in seen_tool_calls:
                                            if is_local:
                                                print(f"   ⏭️  Skipping duplicate tool call: {tool_name}")
                                            continue
                                        
                                        seen_tool_calls.add(tool_call_key)
                                        
                                        # Log tool call
                                        tool_event = logger.log_tool_call(
                                            tool_name=tool_name,
                                            args=tool_args,
                                            session_id=session_id,
                                            message_id=message_id,
                                        )
                                        tool_calls_tracked.append(tool_event)
                                        
                                        # Local logging
                                        if is_local:
                                            try:
                                                args_preview = json.dumps(tool_args)[:200] + "..." if len(json.dumps(tool_args)) > 200 else json.dumps(tool_args)
                                            except (TypeError, ValueError):
                                                args_preview = str(tool_args)[:200] + "..." if len(str(tool_args)) > 200 else str(tool_args)
                                            print(f"\n🔧 [TOOL] Executing: {tool_name}")
                                            print(f"   Args: {args_preview}")
                                        
                                        # Stream tool call to frontend
                                        yield f"data: {json.dumps({'type': 'tool_call', 'name': tool_name, 'args': tool_args})}\n\n"
                            
                            # Extract and stream text content
                            text_content = ""
                            if isinstance(agent_message.content, str):
                                text_content = agent_message.content
                            elif isinstance(agent_message.content, list):
                                for item in agent_message.content:
                                    if isinstance(item, dict):
                                        if item.get('type') == 'text':
                                            text_content += item.get('text', '')
                                        elif item.get('type') == 'tool_use':
                                            # Also handle tool_use in content (Anthropic format)
                                            # Note: This is the same tool call, just in different format
                                            tool_name = item.get('name')
                                            tool_args = item.get('input', {})
                                            if tool_name:
                                                # Check if we've already seen this tool call
                                                tool_call_key = get_tool_call_key(tool_name, tool_args)
                                                if tool_call_key in seen_tool_calls:
                                                    if is_local:
                                                        print(f"   ⏭️  Skipping duplicate tool_use: {tool_name}")
                                                    continue
                                                
                                                seen_tool_calls.add(tool_call_key)
                                                
                                                tool_event = logger.log_tool_call(
                                                    tool_name=tool_name,
                                                    args=tool_args,
                                                    session_id=session_id,
                                                    message_id=message_id,
                                                )
                                                tool_calls_tracked.append(tool_event)
                                                if is_local:
                                                    print(f"\n🔧 [TOOL] Executing (from content): {tool_name}")
                                                yield f"data: {json.dumps({'type': 'tool_call', 'name': tool_name, 'args': tool_args})}\n\n"
                            
                            # Stream text character by character (only new text)
                            if text_content:
                                # Only stream characters we haven't already streamed
                                new_text = text_content[len(full_response):]
                                for char in new_text:
                                    full_response += char
                                    yield f"data: {json.dumps({'type': 'text', 'content': char})}\n\n"
                    
                    # "tools" node contains ToolMessage list (tool results)
                    elif node_name == "tools":
                        if is_local:
                            print(f"   Tool results received: {len(node_output) if isinstance(node_output, list) else 1}")
                        # Tool results are handled internally by the agent, we just log
                        if isinstance(node_output, list):
                            for tool_msg in node_output:
                                if hasattr(tool_msg, 'content') and is_local:
                                    result_preview = str(tool_msg.content)[:150] + "..." if len(str(tool_msg.content)) > 150 else str(tool_msg.content)
                                    print(f"✅ [TOOL] Result received: {result_preview}")
                    
                    # Fallback: handle any list of messages or other formats
                    elif isinstance(node_output, list):
                        # Process tool calls
                        for msg in node_output if isinstance(node_output, list) else [node_output]:
                            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                                for tc in msg.tool_calls:
                                    tool_name = tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', None)
                                    tool_args = tc.get('input', {}) or tc.get('args', {}) if isinstance(tc, dict) else getattr(tc, 'args', {})
                                    
                                    if tool_name:
                                        # Check if we've already seen this tool call
                                        tool_call_key = get_tool_call_key(tool_name, tool_args)
                                        if tool_call_key in seen_tool_calls:
                                            if is_local:
                                                print(f"   ⏭️  Skipping duplicate tool call (fallback): {tool_name}")
                                            continue
                                        
                                        seen_tool_calls.add(tool_call_key)
                                        
                                        # Log tool call for observability
                                        tool_event = logger.log_tool_call(
                                            tool_name=tool_name,
                                            args=tool_args,
                                            session_id=session_id,
                                            message_id=message_id,
                                        )
                                        tool_calls_tracked.append(tool_event)
                                        
                                        # Log for local development
                                        is_local = not os.getenv("VERCEL") and not os.getenv("PRODUCTION")
                                        if is_local:
                                            try:
                                                args_preview = json.dumps(tool_args)[:200] + "..." if len(json.dumps(tool_args)) > 200 else json.dumps(tool_args)
                                            except (TypeError, ValueError):
                                                args_preview = str(tool_args)[:200] + "..." if len(str(tool_args)) > 200 else str(tool_args)
                                            print(f"\n🔧 [TOOL] Executing: {tool_name}")
                                            print(f"   Args: {args_preview}")
                                        
                                        # Stream tool call event to frontend
                                        yield f"data: {json.dumps({'type': 'tool_call', 'name': tool_name, 'args': tool_args})}\n\n"
                            
                            # Extract text content from AI messages
                            elif isinstance(msg, AIMessage):
                                text_content = ""
                                if isinstance(msg.content, str):
                                    text_content = msg.content
                                elif isinstance(msg.content, list):
                                    for item in msg.content:
                                        if isinstance(item, dict) and item.get('type') == 'text':
                                            text_content += item.get('text', '')
                                
                                # Stream text character by character
                                for char in text_content:
                                    full_response += char
                                    yield f"data: {json.dumps({'type': 'text', 'content': char})}\n\n"
                                
                                # Check for tool calls in this message too
                                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                    for tc in msg.tool_calls:
                                        tool_name = tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', None)
                                        tool_args = tc.get('input', {}) or tc.get('args', {}) if isinstance(tc, dict) else getattr(tc, 'args', {})
                                        
                                        if tool_name:
                                            # Check if we've already seen this tool call
                                            tool_call_key = get_tool_call_key(tool_name, tool_args)
                                            if tool_call_key in seen_tool_calls:
                                                if is_local:
                                                    print(f"   ⏭️  Skipping duplicate tool call (msg.tool_calls): {tool_name}")
                                                continue
                                            
                                            seen_tool_calls.add(tool_call_key)
                                            
                                            tool_event = logger.log_tool_call(
                                                tool_name=tool_name,
                                                args=tool_args,
                                                session_id=session_id,
                                                message_id=message_id,
                                            )
                                            tool_calls_tracked.append(tool_event)
                                            
                                            is_local = not os.getenv("VERCEL") and not os.getenv("PRODUCTION")
                                            if is_local:
                                                try:
                                                    args_preview = json.dumps(tool_args)[:200] + "..." if len(json.dumps(tool_args)) > 200 else json.dumps(tool_args)
                                                except (TypeError, ValueError):
                                                    args_preview = str(tool_args)[:200] + "..." if len(str(tool_args)) > 200 else str(tool_args)
                                                print(f"\n🔧 [TOOL] Executing: {tool_name}")
                                                print(f"   Args: {args_preview}")
                                            
                                            yield f"data: {json.dumps({'type': 'tool_call', 'name': tool_name, 'args': tool_args})}\n\n"
                    
                    # Note: "agent" node is already handled above at line 262
                    # This legacy code path is removed to prevent duplicate processing
                                    
        except Exception as e:
            logger.logger.error(f"Error in agent stream: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'text', 'content': f'Error: {str(e)}'})}\n\n"
        
        # Log the complete response
        response_time_ms = (time.time() - start_time) * 1000
        logger.log_response(
            session_id=session_id,
            message_id=message_id,
            user_message=request.message,
            agent_response=full_response,
            tool_calls=tool_calls_tracked,
            response_time_ms=response_time_ms,
            is_first_message=is_first_message,
        )
        
        # Update session with final response
        session["messages"].append({"role": "assistant", "content": full_response})
        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """Clear a session."""
    if session_id in sessions:
        del sessions[session_id]
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/metrics")
def get_metrics():
    """Get observability metrics."""
    return {
        "sessions": {
            sid: logger.get_session_summary(sid)
            for sid in logger.sessions.keys()
        },
        "summary": {
            "total_sessions": len(logger.sessions),
            "total_events": len(logger.events),
            "protocol_violations": sum(
                1 for e in logger.events 
                if e.followed_clarification_protocol is False
            ),
        }
    }


@app.get("/metrics/session/{session_id}")
def get_session_metrics(session_id: str):
    """Get metrics for a specific session."""
    summary = logger.get_session_summary(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")
    return summary


@app.post("/metrics/export")
def export_metrics():
    """Export all metrics to JSON file."""
    output_path = logger.export_metrics()
    return {"status": "exported", "path": str(output_path)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8123)
