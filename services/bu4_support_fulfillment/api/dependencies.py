from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from common.database.client import get_database
from dao.ticket_dao import TicketDAO
from service.ticket_service import TicketService


def get_db() -> AsyncIOMotorDatabase:
    return get_database()


def get_ticket_dao(db: AsyncIOMotorDatabase = Depends(get_db)) -> TicketDAO:
    return TicketDAO(db)


def get_ticket_service(ticket_dao: TicketDAO = Depends(get_ticket_dao)) -> TicketService:
    return TicketService(ticket_dao)
