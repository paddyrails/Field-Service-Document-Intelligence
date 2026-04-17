"""
RiteCare Agent API — exposes the LangGraph agent over HTTP.

POST /query  →  runs the agent and returns the response.
GET  /health →  liveness check.
"""

import uuid

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware  
import json

from agent.graph import agent
from agent_api.dependencies import get_conversation_service
from service.conversation_service import ConversationService

app = FastAPI(title="RiteCare Agent API", version="0.1.0")

app.add_middleware(                                                             
      CORSMiddleware,                                                             
      allow_origins=["http://localhost:3000", "http://localhost:3001"],           
      allow_credentials=True,                                                     
      allow_methods=["*"],                                                        
      allow_headers=["*"],                                                        
  ) 

class QueryRequest(BaseModel):
    query: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    channel: str = "cli"
    user_id: str = "anonymous"
    bu_hint: str | None = None   # set by slack_gateway when channel maps to a known BU


class QueryResponse(BaseModel):
    response: str
    session_id: str

class ResumeRequest(BaseModel):
    session_id: str

class UpdateStateRequest(BaseModel):
    session_id: str
    intent: str | None = None
    approval: bool = True


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    conv_service: ConversationService = Depends(get_conversation_service),
) -> QueryResponse:
    # history = await conv_service.load_history(request.session_id)

    config = {"configurable": {"thread_id": request.session_id}}

    state = {
        "messages": [HumanMessage(content=request.query)],
        "intent": "",
        "session_id": request.session_id,
        "channel": request.channel,
        "bu_hint": request.bu_hint or "",
    }

    result = await agent.ainvoke(state, config)

    #graph paused at interrupt -return what was classifed for review
    current = await agent.aget_state(config)
    if current.next: # graph is paused not finished
        return QueryResponse(
            response=f"[AWAITING APPROVAL] Intent: {result.get('intent', '')}"
                f"Call POST /resume to continue or POST /update-state to modify",
            session_id=request.session_id
        )

    response = result.get("final_response", "Sorry, I could not generate a response.")

    return QueryResponse(response=response, session_id=request.session_id)

@app.post("/update-state")
async def update_state(request: UpdateStateRequest):
    """Modify the paused state before resuming (e.g change the intent or cancel)"""
    config = {"configurable": {"thread_id": request.session_id}}

    current = await agent.aget_state(config)
    if not current.next:
        return {"error": "No paused execution for this session"}
    
    if not request.approval:
        #cancel update to blokced and resume so it hits END
        await agent.aupdate_state(config, {"blocked": True, "final_response": "Execution cancelled by reviewr"})
        result = agent.ainvoke(None, config)
        return {"status": "cancelled", "response": result.get("final_response", "")}
    
    if request.intent:
        await agent.aupdate_state(config, {"intent": request.intent})

    return {"status": "state_updated", "message": "Call POST /resume to continue"}


@app.post("/resume", response_model=QueryResponse)
async def resume(
    request: ResumeRequest
):
    """Resumer a pasued graph execution after human review."""
    config = {"configurable": {"thread_id": request.session_id}}

    
    current = await agent.aget_state(config)
    if not current.next:
        return QueryResponse(response="No paused execution to resume", session_id=request.session_id)
    
    result = await agent.ainvoke(None, config)
    response = result.get("final_response", "Sorry I could not generate response")

    return QueryResponse(response=response, session_id=request.session_id)


@app.post("/query/stream")
async def query_stream(request: QueryRequest):
    """Stream agent request token-by-token via Server-Sent Events"""
    config = {"configurable": {"thread_id": request.session_id}}

    state = {
        "messages": [HumanMessage(content=request.query)],
        "intent": "",
        "session_id": request.session_id,
        "channel": request.channel,
        "bu_hint": request.bu_hint or ""
    }

    async def event_generator():
        #stream node updates +LLM tokens
        async for event, data in agent.astream(state, config, stream_mode=["updates", "messages"]):
            if event == "updtes":
                #Node completeted - send which node just ran
                for node_name, node_output in data.items():
                    yield f"event: node\ndata: {json.dumps({'node': node_name})}\n\n"

            elif event == "messages":
                # LLM tocken chunk
                message, metadata = data
                if isinstance(message, AIMessageChunk) and message.content:
                    yield f"event: token\n data: {json.dumps({'token': message.content,
                                     'node': metadata.get('langgraph_node', '')})}\n\n"
                    
        yield "event: done \n data: {}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "n"}
    )




@app.get("/history/{session_id}")
async def get_state_history(session_id: str):
    """Replay all intermediate states for a session (time travel debugging)"""
    config = {"configurable": {"thread_id": session_id}}

    snapshots = []
    async for state in agent.aget_state_history(config):
        snapshots.append({
            "checkpoint_id": state.config["configurable"].get("checkpoint_id"),
            "node": state.metadata.get("source", "unknown"),
            "step": state.metadata.get("step", -1),
            "blocked": state.metadata.get("blocked"),
            "intent": state.metadata.get("intent"),
            "tool_results_count": len(state.metadata.get("tool_results", [])),
            "final_response": state.metadata.get("final_response", ""),
            "grounding_retries": state.metadata.get("grounding_retries", 0),
            "message_count": len(state.metadata.get("messages", []))
        })
    return {"session_id": session_id, "check_points": snapshots}

@app.get("/state/{session_id}")                                             
async def get_current_state(session_id: str):                                 
    """Get the latest state snapshot for a session."""
    config = {"configurable": {"thread_id": session_id}}                      
                                                                            
    state = await agent.aget_state(config)  
                                                                            
    if not state.values:
        return {"error": f"No state found for session {session_id}"}          
                                                                            
    return {                                                                  
        "session_id": session_id,                                           
        "checkpoint_id": state.config["configurable"].get("checkpoint_id"),
        "node": state.next,  # which node would run next (empty if done)
        "values": {                         
            "blocked": state.values.get("blocked"),                           
            "intent": state.values.get("intent", ""),
            "final_response": state.values.get("final_response", ""),         
            "grounding_retries": state.values.get("grounding_retries", 0),  
            "message_count": len(state.values.get("messages", [])),           
            "tool_results": state.values.get("tool_results", []),           
        },                                                                    
    } 







if __name__ == "__main__":
    uvicorn.run("agent_api.main:app", host="0.0.0.0", port=8000, reload=False)
