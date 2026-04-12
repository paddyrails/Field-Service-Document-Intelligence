import httpx

from channel_router import get_channel_name, is_watched
from config import settings


async def handle_message(body: dict, say, client, logger) -> None:
    event = body.get("event", {})

    # Ignore bot messages and message edits/deletions
    if event.get("bot_id") or event.get("subtype"):
        return

    text = event.get("text", "").strip()
    if not text:
        return

    channel_id = event["channel"]
    user_id = event.get("user", "unknown")
    thread_ts = event.get("thread_ts") or event.get("ts")

    # Only respond in the watched back-office channels
    channel_name = await get_channel_name(client, channel_id)
    if not channel_name or not is_watched(channel_name):
        return

    # Stable session key per user per channel — groups a user's conversation
    session_id = f"{channel_name}-{user_id}"

    logger.info(f"Query from {user_id} in #{channel_name}: {text[:80]}")

    try:
        async with httpx.AsyncClient() as http:
            response = await http.post(
                f"{settings.agent_base_url}/query",
                json={
                    "query": text,
                    "session_id": session_id,
                    "channel": channel_name,
                    "user_id": user_id,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            agent_reply = response.json()["response"]
    except Exception as e:
        logger.error(f"Agent API error: {e}")
        agent_reply = "Sorry, I encountered an error processing your request. Please try again."

    await say(text=agent_reply, thread_ts=thread_ts)
