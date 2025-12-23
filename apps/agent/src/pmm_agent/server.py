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
from pydantic import BaseModel

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableLambda

from .prompts import MAIN_SYSTEM_PROMPT
from .tools import ALL_TOOLS
from .observability import get_logger

# Create a tool lookup for execution
TOOL_MAP = {tool.name: tool for tool in ALL_TOOLS}

# Configure root_path for Vercel deployment
# Vercel passes /api/* paths, so FastAPI needs to know it's mounted at /api
import os
root_path = "/api" if os.getenv("VERCEL") else ""
app = FastAPI(title="PMM Deep Agent", version="0.1.0", root_path=root_path)

# CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# Initialize model with tools
llm = ChatAnthropic(
    model_name=os.getenv("MODEL", "claude-sonnet-4-20250514"),
    max_tokens=8192,
)
llm_with_tools = llm.bind_tools(ALL_TOOLS)

# Simple in-memory session storage
sessions: dict = {}

# Initialize observability
logger = get_logger()


class ChatRequest(BaseModel):
    message: str
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

    # Call Claude
    messages = [
        HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"])
        for m in session["messages"] if m["role"] != "system"
    ]

    response = await llm_with_tools.ainvoke(
        [{"role": "system", "content": MAIN_SYSTEM_PROMPT}] + messages
    )

    # Extract response
    response_text = response.content if isinstance(response.content, str) else ""
    tool_calls = None

    if hasattr(response, 'tool_calls') and response.tool_calls:
        tool_calls = [
            {"name": tc["name"], "args": tc["args"]}
            for tc in response.tool_calls
        ]
        # For tool calls, format as text
        if not response_text:
            response_text = f"Using tools: {', '.join(tc['name'] for tc in tool_calls)}"

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

    # Generate unique message ID for tracking
    message_id = str(uuid.uuid4())
    start_time = time.time()
    tool_calls_tracked = []

    async def generate() -> AsyncGenerator[str, None]:
        messages = [
            HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"])
            for m in session["messages"] if m["role"] != "system"
        ]

        full_response = ""
        current_messages = messages.copy()
        max_iterations = 10  # Prevent infinite loops
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            tool_calls_in_this_round = []
            ai_message_content = ""
            
            # Track tool calls to avoid duplicates
            seen_tool_calls = set()
            
            # Get the complete AI response (properly formatted by LangChain)
            # This avoids issues with manually merging chunks that contain invalid content types
            try:
                ai_message = await llm_with_tools.ainvoke(
                    [{"role": "system", "content": MAIN_SYSTEM_PROMPT}] + current_messages
                )
            except Exception as e:
                logger.logger.error(f"Error getting AI response: {e}")
                yield f"data: {json.dumps({'type': 'text', 'content': f'Error: {str(e)}'})}\n\n"
                break
            
            # Extract tool calls from the message
            if hasattr(ai_message, 'tool_calls') and ai_message.tool_calls:
                for tc in ai_message.tool_calls:
                    tool_name = tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', None)
                    tool_args = tc.get('input', {}) or tc.get('args', {}) if isinstance(tc, dict) else getattr(tc, 'args', {})
                    tool_call_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                    
                    if tool_name and tool_call_id:
                        # Log tool call
                        tool_event = logger.log_tool_call(
                            tool_name=tool_name,
                            args=tool_args,
                            session_id=session_id,
                            message_id=message_id,
                        )
                        tool_calls_tracked.append(tool_event)
                        
                        # Store for execution
                        tool_calls_in_this_round.append({
                            'id': tool_call_id,
                            'name': tool_name,
                            'args': tool_args
                        })
                        
                        yield f"data: {json.dumps({'type': 'tool_call', 'name': tool_name, 'args': tool_args})}\n\n"
            
            # Also check content list for tool_use items (Anthropic format)
            if hasattr(ai_message, 'content') and isinstance(ai_message.content, list):
                for item in ai_message.content:
                    if isinstance(item, dict) and item.get('type') == 'tool_use':
                        tool_name = item.get('name')
                        tool_args = item.get('input', {})
                        tool_call_id = item.get('id')
                        
                        if tool_name and tool_call_id and tool_call_id not in [tc.get('id') for tc in tool_calls_in_this_round]:
                            # Log tool call
                            tool_event = logger.log_tool_call(
                                tool_name=tool_name,
                                args=tool_args,
                                session_id=session_id,
                                message_id=message_id,
                            )
                            tool_calls_tracked.append(tool_event)
                            
                            # Store for execution
                            tool_calls_in_this_round.append({
                                'id': tool_call_id,
                                'name': tool_name,
                                'args': tool_args
                            })
                            
                            yield f"data: {json.dumps({'type': 'tool_call', 'name': tool_name, 'args': tool_args})}\n\n"
            
            # Stream the text content character by character for frontend
            text_content = ""
            if hasattr(ai_message, 'content'):
                if isinstance(ai_message.content, str):
                    text_content = ai_message.content
                elif isinstance(ai_message.content, list):
                    # Extract text from content list
                    for item in ai_message.content:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            text_content += item.get('text', '')
            
            # Stream text character by character
            for char in text_content:
                full_response += char
                yield f"data: {json.dumps({'type': 'text', 'content': char})}\n\n"
            
            # Add AI message to conversation
            current_messages.append(ai_message)
            
            # If no tool calls, we're done
            if not tool_calls_in_this_round:
                break
            
            # Execute tools and get results
            # Extract tool calls directly from the AI message to ensure correct IDs
            tool_calls_to_execute = []
            if ai_message:
                if hasattr(ai_message, 'tool_calls') and ai_message.tool_calls:
                    tool_calls_to_execute = ai_message.tool_calls
                elif hasattr(ai_message, 'content') and isinstance(ai_message.content, list):
                    # Extract from content list (Anthropic format)
                    for item in ai_message.content:
                        if isinstance(item, dict) and item.get('type') == 'tool_use':
                            tool_calls_to_execute.append(item)
            
            tool_messages = []
            for tc in tool_calls_to_execute:
                # Get the actual tool call data from the message
                tool_call_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                tool_name = tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', None)
                tool_args = tc.get('input', {}) or tc.get('args', {}) if isinstance(tc, dict) else getattr(tc, 'args', {})
                
                if not tool_name:
                    continue
                
                # If tool_args is empty, try to extract from conversation context
                if not tool_args and tool_name == 'analyze_product':
                    # Extract product description from recent user messages
                    user_messages = [m for m in current_messages if isinstance(m, HumanMessage)]
                    if user_messages:
                        # Use the most recent user message as product description
                        tool_args = {
                            'product_description': user_messages[-1].content
                        }
                        logger.logger.warning(
                            f"[TOOL] {tool_name} called with empty args, extracted from conversation context"
                        )
                
                if tool_name in TOOL_MAP:
                    try:
                        # Execute the tool
                        tool = TOOL_MAP[tool_name]
                        if hasattr(tool, 'ainvoke'):
                            tool_result = await tool.ainvoke(tool_args)
                        else:
                            tool_result = tool.invoke(tool_args)
                        
                        # Log tool result
                        logger.log_tool_call(
                            tool_name=tool_name,
                            args=tool_args,
                            session_id=session_id,
                            message_id=message_id,
                            result=str(tool_result)[:200],  # Log first 200 chars
                        )
                        
                        # Create ToolMessage with result - use simple string format
                        tool_messages.append(
                            ToolMessage(
                                content=str(tool_result),
                                tool_call_id=tool_call_id
                            )
                        )
                    except Exception as e:
                        # Log error
                        error_msg = str(e)
                        logger.log_tool_call(
                            tool_name=tool_name,
                            args=tool_args,
                            session_id=session_id,
                            message_id=message_id,
                            error=error_msg,
                        )
                        tool_messages.append(
                            ToolMessage(
                                content=f"Error: {error_msg}",
                                tool_call_id=tool_call_id
                            )
                        )
            
            # Add tool results to messages for next iteration
            if tool_messages:
                current_messages.extend(tool_messages)
                # Continue loop to get LLM response with tool results
                # Reset for next iteration
                full_response = ""  # Will accumulate new response
                ai_message_content = ""
                # Use ainvoke for follow-up to avoid streaming complexity
                try:
                    follow_up_response = await llm_with_tools.ainvoke(
                        [{"role": "system", "content": MAIN_SYSTEM_PROMPT}] + current_messages
                    )
                    # Extract text content properly (handle both str and list formats)
                    follow_up_text = ""
                    if hasattr(follow_up_response, 'content'):
                        if isinstance(follow_up_response.content, str):
                            follow_up_text = follow_up_response.content
                        elif isinstance(follow_up_response.content, list):
                            # Extract text from content list
                            for item in follow_up_response.content:
                                if isinstance(item, dict) and item.get('type') == 'text':
                                    follow_up_text += item.get('text', '')
                    
                    # Stream the follow-up response character by character
                    for char in follow_up_text:
                        full_response += char
                        yield f"data: {json.dumps({'type': 'text', 'content': char})}\n\n"
                    current_messages.append(follow_up_response)
                    break  # Done after follow-up
                except Exception as e:
                    logger.logger.error(f"Error getting follow-up response: {e}")
                    break
            else:
                # No tool messages means tools failed, break to avoid infinite loop
                break

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
