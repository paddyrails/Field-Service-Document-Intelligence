from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from common.database.client import get_database
from dao.customer_dao import CustomerDAO
from dao.vector_dao import VectorDAO
from service.customer_service import CustomerService


def get_db() -> AsyncIOMotorDatabase:
    return get_database()


def get_customer_dao(db: AsyncIOMotorDatabase = Depends(get_db)) -> CustomerDAO:
    return CustomerDAO(db)


def get_vector_dao(db: AsyncIOMotorDatabase = Depends(get_db)) -> VectorDAO:
    return VectorDAO(db)


def get_customer_service(
    customer_dao: CustomerDAO = Depends(get_customer_dao),
    vector_dao: VectorDAO = Depends(get_vector_dao),
) -> CustomerService:
    return CustomerService(customer_dao, vector_dao)
