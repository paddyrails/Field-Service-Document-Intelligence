import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.router import router
from common.config import settings
from common.database.client import close_client, get_database
from common.exceptions.handlers import VisitNotFoundError, visit_not_found_handler
from common.kafka.consumer import AppointmentConsumer
from common.limiter.rate_limiter import limiter
from common.logging.logger import setup_logging
from common.slack.notifier import SlackNotifier
from dao.vector_dao import VectorDAO
from dao.visit_dao import VisitDAO
from service.visit_service import VisitService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()

    db = get_database()
    visit_dao = VisitDAO(db)
    vector_dao = VectorDAO(db)
    slack_notifier = SlackNotifier(settings.slack_bot_token, settings.slack_members_channel)
    visit_service = VisitService(visit_dao, vector_dao, slack_notifier)

    consumer = AppointmentConsumer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        topic=settings.kafka_topic,
        group_id=settings.kafka_group_id,
    )
    await consumer.start()
    consume_task = asyncio.create_task(
        consumer.consume(visit_service.handle_appointment_event)
    )

    yield

    consume_task.cancel()
    await consumer.stop()
    await close_client()


app = FastAPI(
    title="RiteCare BU5 - Care Operations",
    description="API for managing patient visits and care preparation documentation",
    version="0.1.0",
    root_path="/bu5",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(VisitNotFoundError, visit_not_found_handler)

app.include_router(router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "service": "bu5-care-operations"}
