from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from common.database.client import get_database
from dao.invoice_dao import InvoiceDAO
from dao.subscription_dao import SubscriptionDAO
from service.invoice_service import InvoiceService
from service.subscription_service import SubscriptionService


def get_db() -> AsyncIOMotorDatabase:
    return get_database()


def get_invoice_dao(db: AsyncIOMotorDatabase = Depends(get_db)) -> InvoiceDAO:
    return InvoiceDAO(db)


def get_subscription_dao(db: AsyncIOMotorDatabase = Depends(get_db)) -> SubscriptionDAO:
    return SubscriptionDAO(db)


def get_invoice_service(invoice_dao: InvoiceDAO = Depends(get_invoice_dao)) -> InvoiceService:
    return InvoiceService(invoice_dao)


def get_subscription_service(
    subscription_dao: SubscriptionDAO = Depends(get_subscription_dao),
) -> SubscriptionService:
    return SubscriptionService(subscription_dao)
