import json 

from agent.state import AgentState
from shared.guardrails import check_grounding, redact_pii

#Tool-result "type values from tool_executor that represent retrived docs"
RAG_RESULT_TYPES = {"RAG", "rag", "search"}

def _extract_retrieved_docs(tool_results: list[dict]) -> list[str]:
    """
    Pull text chunks out of RAG tool results for grounding checks
    """
    docs: list[str] = []
    for item in tool_results or []:
        if item.get("type", "").upper() not in {t.upper() for t in RAG_RESULT_TYPES}:
            continue
        result = item.get("result")
        if isinstance(result, list):                                            
            docs.extend(str(d.get("text", d)) if isinstance(d, dict) else str(d) for d in result)                                                               
        elif isinstance(result, dict) and "results" in result:                
            docs.extend(
                str(d.get("text", d)) if isinstance(d, dict) else str(d)
                for d in result["results"]
            )                                                    
        elif result is not None:
            docs.append(str(result))                                            
    return docs 

async def output_guardrail(state: AgentState) -> dict:
    """Redact PII and ground-check the response against retrieved context"""
    final = state.get("final_response", "") or ""
    if not final:
        return {}
    
    #PII redaction
    final = redact_pii(final)

    #Grounding check only if RAG docs were retrived this turn
    docs = _extract_retrieved_docs(state.get("tool_results", []))
    if docs and final.strip():
        verdict = await check_grounding(final, docs)
        if not verdict.get("grounded", True):
            final += f"\n\n[Ungrounded: {verdict.get('reason', 'no reason given')}]"

    return {"final_response": final}