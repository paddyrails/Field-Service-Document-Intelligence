"""
RiteCare Slack Gateway

Listens for messages in the three back-office Slack channels using Socket Mode
(no public URL required) and forwards them to the RiteCare Agent API.

Required Slack app scopes:
  Bot Token Scopes:  channels:history, channels:read, chat:write
  App-Level Token:   connections:write  (for Socket Mode)

Usage:
    uv run python main.py
"""

import asyncio
import logging

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler

from config import settings
from handlers import handle_claim_action, handle_message


app = AsyncApp(token=settings.slack_bot_token)
app.event("message")(handle_message)
app.action("claim_visit")(handle_claim_action)


async def main() -> None:
    handler = AsyncSocketModeHandler(app, settings.slack_app_token)
    await handler.start_async()


if __name__ == "__main__":
    logging.basicConfig(level=settings.log_level)
    asyncio.run(main())
