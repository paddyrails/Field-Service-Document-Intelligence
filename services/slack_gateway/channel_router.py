# Slack channels this gateway listens to, mapped to their BU.
# Channel names (without #) must match exactly what is configured in Slack.
CHANNEL_BU_MAP: dict[str, str] = {
    "rc_help_customer_profile_backoffice": "BU1",
    "rc_help_sales_backoffice": "BU2",
    "rc_help_billing_fulfillment_backoffice": "BU3",
    "rc_help_support_backoffice": "BU4",
    "rc_care_members": "BU5",
}

WATCHED_CHANNELS = set(CHANNEL_BU_MAP.keys())


async def get_channel_name(client, channel_id: str) -> str | None:
    """Resolves a Slack channel ID (e.g. C1234ABCD) to its name."""
    try:
        result = await client.conversations_info(channel=channel_id)
        return result["channel"]["name"]
    except Exception:
        return None


def is_watched(channel_name: str) -> bool:
    return channel_name in WATCHED_CHANNELS


def get_bu(channel_name: str) -> str | None:
    """Returns the BU for a channel, or None if unmapped."""
    return CHANNEL_BU_MAP.get(channel_name)
