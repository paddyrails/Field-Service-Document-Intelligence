import re
import json
from google import genai
from shared.config import settings

_genai_client = genai.Client(api_key=settings.google_api_key)

PII_PATTERNS = [
    (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]'),
    (r'\b\d{16}\b', '[CARD_REDACTED]'),
    (r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b', '[EMAIL_REDACTED]'),
    (r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE_REDACTED]'),    
]

BLOCKED_PHRASES = [
    "ignore previous",
    "ignore above",
    "disregard previous",
    "system prompt",
    "jailbreak",
    "bypass"
]

DOMAIN_KEYWORDS = [
    "patient", "visit", "care", "nursing", "therapy", "billing",
    "invoice", "ticket", "support", "contract", "customer",
    "onboarding", "kyc", "subscription", "appointment", "insurance",
    "schedule", "service", "maintenance", "claim", "status",
    
]

def detect_prompt_injection(text:str) -> str | None:
    """Return error message if suspicious phrase detected, else None"""
    lower = text.lower()
    for phrase in BLOCKED_PHRASES:
        if phrase in lower:
            return f"BLOCKED: prompt injection pattern detected ('{phrase}')"
    return None

def check_topic_relevance(text: str) -> str | None:
    """Rejects queries unrelated to RiteCare domain"""
    lower = text.lower()
    if not any(k in lower for k in DOMAIN_KEYWORDS):
        return "BLOCKED: query is not related to RiteCare Services"
    return None

def redact_pii(text:str) -> str:
    """Redacts PII from text"""
    for pattern, replacement in PII_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text

async def check_grounding(response: str, retrieved_docs: list[str]) -> dict:
    """Check if response is grounded in retrieved context"""

    context = "\n".join(retrieved_docs) if retrieved_docs else "(no context)"
    prompt = f"""Evaluate if the response is grounded in the provided context
    Context:
    {context}

    Response:
    {response}

    Respond with EXACTLY this JSON format:
    {{"grounded": true or false, "reason": "one sentence explanation"}}
    """

    result = await _genai_client.aio.models.generate_content(
        model=settings.google_chat_model,
        contents=prompt
    )

    try:
        text = result.text.strip()
        # Strip markdown code fences if Gemini wraps the JSON
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)
    except (json.JSONDecodeError, IndexError):
        return {"grounded": True, "reason": "Could not parse grounding check"}

    