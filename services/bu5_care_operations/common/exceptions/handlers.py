from fastapi import Request
from fastapi.responses import JSONResponse


class VisitNotFoundError(Exception):
    def __init__(self, visit_id: str) -> None:
        self.visit_id = visit_id


async def visit_not_found_handler(
    request: Request, exc: VisitNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": f"Visit '{exc.visit_id}' not found"},
    )
