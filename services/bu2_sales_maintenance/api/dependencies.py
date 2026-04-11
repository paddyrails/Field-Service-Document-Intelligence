from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from common.database.client import get_database
from dao.contract_dao import ContractDAO
from dao.visit_dao import VisitDAO
from service.contract_service import ContractService
from service.visit_service import VisitService


def get_db() -> AsyncIOMotorDatabase:
    return get_database()


def get_contract_dao(db: AsyncIOMotorDatabase = Depends(get_db)) -> ContractDAO:
    return ContractDAO(db)


def get_visit_dao(db: AsyncIOMotorDatabase = Depends(get_db)) -> VisitDAO:
    return VisitDAO(db)


def get_contract_service(contract_dao: ContractDAO = Depends(get_contract_dao)) -> ContractService:
    return ContractService(contract_dao)


def get_visit_service(visit_dao: VisitDAO = Depends(get_visit_dao)) -> VisitService:
    return VisitService(visit_dao)
