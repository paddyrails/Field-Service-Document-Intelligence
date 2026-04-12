from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from common.config import settings
from common.database.client import get_database
from common.slack.notifier import SlackNotifier
from dao.vector_dao import VectorDAO
from dao.visit_dao import VisitDAO
from service.visit_service import VisitService


def get_db() -> AsyncIOMotorDatabase:
    return get_database()


def get_visit_dao(db: AsyncIOMotorDatabase = Depends(get_db)) -> VisitDAO:
    return VisitDAO(db)


def get_vector_dao(db: AsyncIOMotorDatabase = Depends(get_db)) -> VectorDAO:
    return VectorDAO(db)


def get_slack_notifier() -> SlackNotifier:
    return SlackNotifier(settings.slack_bot_token, settings.slack_members_channel)


def get_visit_service(
    visit_dao: VisitDAO = Depends(get_visit_dao),
    vector_dao: VectorDAO = Depends(get_vector_dao),
    slack_notifier: SlackNotifier = Depends(get_slack_notifier),
) -> VisitService:
    return VisitService(visit_dao, vector_dao, slack_notifier)
