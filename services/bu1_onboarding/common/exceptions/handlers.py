from fastapi import Request
from fastapi.responses import JSONResponse

class CustomerNotFoundError(Exception):
    def __init__(self, customer_id:str) -> None:
        self.customer_id = customer_id

class DuplicateCustomerError(Exception):
    def __init__(self, email:str) -> None:
        self.email = email        

async def customer_not_found_handler(
        request: Request, exc: CustomerNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={'detail': f"Customer '{exc.customer_id}' not found"}
    )

async def duplicate_customer_handler(
     request: Request, exc: DuplicateCustomerError   
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={'detail': f"Customer with '{exc.email}' already exists"}
    )
        