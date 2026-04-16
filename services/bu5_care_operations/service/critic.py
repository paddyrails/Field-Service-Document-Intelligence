from google import genai
from common.config import settings

_client = genai.Client(api_key=settings.google_api_key)

MAX_RETRIES = 3

async def evaluate_relevance(
        query: str,
        notes: str,
        service_type: str,
        retrieved_texts: list[str]
) -> dict:
    context = "\n--\n".join(retrieved_texts) if retrieved_texts else "(no results)"

    prompt = f"""You are a retrieval quality evaluator for a healthchare field service company.
    Query: {query}
    Patient notes: {notes}
    Service type: {service_type}

    Retrieved context:
    {context}

    Evaluate if the retrieved context is specifically relevant to the patient's condition
    described in the notes.
    Score from 0-10 where:
    - 10 = perfectly matches the specific condition in notes
    - 7 = reasonably relevant to the condition
    - 4 = generic/tangentially related
    - 0 = completely irrelevant

    Response in EXACTLY this format:
    SCORE: <number>
    VERDICT: <PASS or FAIL>
    REASON: <one sentence explanation>
    """

    response = _client.models.generate_content(
        model=settings.google_chat_model,
        contents=prompt
    )

    return _parse_response(response.text.strip())

async def rewrite_query(
        original_query: str,
        notes: str,
        service_type: str,
        failure_reason: str
) -> str:
    prompt = f"""The following search query failed to retrieve relevant results
    for a patient care visit.

    Original query: {original_query}
    Patient notes: {notes}
    Service type: {service_type}
    Failure reason: {failure_reason}

    Rewrite the query to be more specific to the patient's condition.
    Focus on the specific body part, condition, or treatment mentioned in the notes.
    Reply with only the rewritten query, nothing else
    """
    response = _client.models.generate_content(
        model=settings.google_chat_model,
        contents=prompt
    )

    return response.text.strip()



def _parse_response(text: str) -> dict:
    result = {"verdict": "FAIL", "score": 0, "reason": "Could not parse critic response"}

    for line in text.split("\n"):
        line = line.strip()
        if line.upper().startswith("SCORE:"):
            try:
                result["score"] = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.upper().startswith("VERDICT:"):
            verdict = line.split(":", 1)[1].strip().upper()
            result["verdict"] = "PASS" if "PASS" in verdict else "FAIL"
        elif line.upper().startswith("REASON"):
            result["reason"] = line.split(":", 1)[1].strip()

    return result

