import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.router import router
from common.config import settings
from common.kafka.producer import close_producer, get_producer


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logging.basicConfig(level=settings.log_level)
    await get_producer()   # warm up connection on startup
    yield
    await close_producer()


app = FastAPI(
    title="RiteCare Appointment Service",
    description="Books patient appointments and publishes events to Kafka",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "service": "appointment-service"}
