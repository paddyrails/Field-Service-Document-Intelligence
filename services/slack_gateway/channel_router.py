# The three back-office Slack channels this gateway listens to.
# Channel names (without #) must match exactly what is configured in Slack.
WATCHED_CHANNELS = {
    "rc_help_sales_backoffice",
    "rc_help_customer_profile_backoffice",
    "rc_help_billing_fulfillment_backoffice",
}


async def get_channel_name(client, channel_id: str) -> str | None:
    """Resolves a Slack channel ID (e.g. C1234ABCD) to its name."""
    try:
        result = await client.conversations_info(channel=channel_id)
        return result["channel"]["name"]
    except Exception:
        return None


def is_watched(channel_name: str) -> bool:
    """Returns True if this channel is one the gateway should respond to."""
    return channel_name in WATCHED_CHANNELS
