from fastapi import Request
from fastapi.responses import JSONResponse


class TicketNotFoundError(Exception):
    def __init__(self, ticket_id: str) -> None:
        self.ticket_id = ticket_id


class TicketAlreadyClosedError(Exception):
    def __init__(self, ticket_id: str) -> None:
        self.ticket_id = ticket_id


async def ticket_not_found_handler(
    request: Request, exc: TicketNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": f"Ticket '{exc.ticket_id}' not found"},
    )


async def ticket_already_closed_handler(
    request: Request, exc: TicketAlreadyClosedError
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": f"Ticket '{exc.ticket_id}' is already closed"},
    )
