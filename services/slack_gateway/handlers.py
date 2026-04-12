import httpx

from channel_router import get_bu, get_channel_name, is_watched
from config import settings


async def handle_claim_action(ack, body, client, logger) -> None:
    """Handles the 'Claim Visit' button press from the Slack members channel."""
    await ack()

    action = body["actions"][0]
    visit_id = action["value"]
    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]
    message_ts = body["message"]["ts"]

    logger.info(f"User {user_id} claiming visit {visit_id}")

    try:
        async with httpx.AsyncClient() as http:
            response = await http.patch(
                f"{settings.bu5_base_url}/visits/{visit_id}/claim",
                json={"slack_user_id": user_id},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        logger.error(f"Failed to claim visit {visit_id}: {e}")
        await client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text="Failed to claim visit. Please try again.",
        )
        return

    visit = data["visit"]
    instructions = data["care_instructions"]
    service_type = visit["service_type"].replace("-", " ").title()
    scheduled_at = visit["scheduled_at"][:16].replace("T", " at ")

    # Update the original channel message to show it's been claimed
    await client.chat_update(
        channel=channel_id,
        ts=message_ts,
        text=f"Visit claimed by <@{user_id}>",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*{service_type}* visit for *{visit['patient_name']}* "
                        f"on {scheduled_at}\n"
                        f"✅ Claimed by <@{user_id}>"
                    ),
                },
            }
        ],
    )

    # DM the field officer with visit details and care instructions
    dm = await client.conversations_open(users=user_id)
    dm_channel = dm["channel"]["id"]

    instructions_text = (
        "\n".join(f"• {line}" for line in instructions)
        if instructions
        else "_No specific instructions found. Please follow standard protocols._"
    )

    await client.chat_postMessage(
        channel=dm_channel,
        text=f"You have claimed a visit — here are your preparation details.",
        blocks=[
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Your Visit Assignment"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Patient:*\n{visit['patient_name']}"},
                    {"type": "mrkdwn", "text": f"*Service:*\n{service_type}"},
                    {"type": "mrkdwn", "text": f"*Scheduled:*\n{scheduled_at}"},
                    {"type": "mrkdwn", "text": f"*Address:*\n{visit.get('address') or 'TBD'}"},
                ],
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Care Preparation Checklist:*\n{instructions_text}",
                },
            },
        ],
    )


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
            payload: dict = {
                "query": text,
                "session_id": session_id,
                "channel": channel_name,
                "user_id": user_id,
            }
            bu = get_bu(channel_name)
            if bu:
                payload["bu_hint"] = bu

            response = await http.post(
                f"{settings.agent_base_url}/query",
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            agent_reply = response.json()["response"]
    except Exception as e:
        logger.error(f"Agent API error: {e}")
        agent_reply = "Sorry, I encountered an error processing your request. Please try again."

    await say(text=agent_reply, thread_ts=thread_ts)
