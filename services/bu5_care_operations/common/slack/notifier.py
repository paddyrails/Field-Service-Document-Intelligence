import logging
from datetime import datetime

from slack_sdk.web.async_client import AsyncWebClient

logger = logging.getLogger(__name__)


class SlackNotifier:
    def __init__(self, token: str, members_channel: str) -> None:
        self._client = AsyncWebClient(token=token)
        self._channel = members_channel

    async def post_pending_visit(
        self,
        visit_id: str,
        patient_name: str,
        service_type: str,
        scheduled_at: datetime,
        address: str | None,
    ) -> None:
        formatted_time = scheduled_at.strftime("%b %d, %Y at %I:%M %p")
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "New Visit Available"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Patient:*\n{patient_name}"},
                    {"type": "mrkdwn", "text": f"*Service:*\n{service_type.replace('-', ' ').title()}"},
                    {"type": "mrkdwn", "text": f"*Scheduled:*\n{formatted_time}"},
                    {"type": "mrkdwn", "text": f"*Address:*\n{address or 'TBD'}"},
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Claim Visit"},
                        "style": "primary",
                        "action_id": "claim_visit",
                        "value": visit_id,
                    }
                ],
            },
        ]
        try:
            await self._client.chat_postMessage(
                channel=self._channel,
                text=f"New {service_type} visit available for {patient_name} on {formatted_time}",
                blocks=blocks,
            )
        except Exception as e:
            logger.error(f"Failed to post pending visit to Slack: {e}")
