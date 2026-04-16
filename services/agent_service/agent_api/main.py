"""
RiteCare Agent API — exposes the LangGraph agent over HTTP.

POST /query  →  runs the agent and returns the response.
GET  /health →  liveness check.
"""

import uuid

import uvicorn
from fastapi import Depends, FastAPI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware  

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


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    conv_service: ConversationService = Depends(get_conversation_service),
) -> QueryResponse:
    history = await conv_service.load_history(request.session_id)

    state = {
        "messages": history + [HumanMessage(content=request.query)],
        "intent": "",
        "tool_calls": [],
        "tool_results": [],
        "session_id": request.session_id,
        "channel": request.channel,
        "bu_hint": request.bu_hint or "",
        "final_response": "",
    }

    result = await agent.ainvoke(state)
    response = result.get("final_response", "Sorry, I could not generate a response.")

    await conv_service.save_turn(
        session_id=request.session_id,
        channel=request.channel,
        user_id=request.user_id,
        user_text=request.query,
        ai_text=response,
    )

    return QueryResponse(response=response, session_id=request.session_id)


if __name__ == "__main__":
    uvicorn.run("agent_api.main:app", host="0.0.0.0", port=8000, reload=False)
