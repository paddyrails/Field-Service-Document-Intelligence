import asyncio
import json
import logging
from collections.abc import Awaitable, Callable

from aiokafka import AIOKafkaConsumer

logger = logging.getLogger(__name__)


class AppointmentConsumer:
    def __init__(self, bootstrap_servers: str, topic: str, group_id: str) -> None:
        self._consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda v: json.loads(v.decode()),
            auto_offset_reset="earliest",
        )

    async def start(self) -> None:
        await self._consumer.start()
        logger.info("Kafka consumer started")

    async def stop(self) -> None:
        await self._consumer.stop()
        logger.info("Kafka consumer stopped")

    async def consume(self, handler: Callable[[dict], Awaitable[None]]) -> None:
        try:
            async for msg in self._consumer:
                try:
                    await handler(msg.value)
                except Exception as e:
                    logger.error(f"Error handling appointment event: {e}")
        except asyncio.CancelledError:
            pass
