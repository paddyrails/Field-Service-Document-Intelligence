import httpx
from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel

from api.dependencies import get_orchestrator
from common.config import settings
from service.ingestion_orchestrator import IngestionOrchestrator

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    dag_run_id: str
    file_path: str
    status: str = "queued"


class NotifyRequest(BaseModel):
    dag_run_id: str
    bu: str
    status: str          # "success" | "failed"
    chunks_stored: int = 0
    error: str = ""


class StatusResponse(BaseModel):
    dag_run_id: str
    state: str           # Airflow states: queued, running, success, failed


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/ingest", response_model=IngestResponse)
async def ingest(
    file: UploadFile = File(...),
    bu: str = Form(...),
    customer_id: str = Form(""),
    service_type: str = Form(""),
    orchestrator: IngestionOrchestrator = Depends(get_orchestrator),
) -> IngestResponse:
    """Accept a file upload, save it, and trigger an Airflow DAG run."""
    file_bytes = await file.read()
    result = await orchestrator.trigger(file_bytes, file.filename, bu, customer_id, service_type)
    return IngestResponse(**result)


@router.post("/ingest/notify")
async def notify(request: NotifyRequest) -> dict:
    """Called by Airflow on DAG completion — sends a Slack notification."""
    if settings.slack_webhook_url:
        if request.status == "success":
            text = (
                f"Ingestion complete — {request.bu} | "
                f"{request.chunks_stored} chunks stored | run: {request.dag_run_id}"
            )
        else:
            text = (
                f"Ingestion failed — {request.bu} | "
                f"error: {request.error} | run: {request.dag_run_id}"
            )
        async with httpx.AsyncClient() as client:
            await client.post(settings.slack_webhook_url, json={"text": text})

    return {"received": True}


@router.get("/ingest/{dag_run_id}/status", response_model=StatusResponse)
async def get_status(dag_run_id: str) -> StatusResponse:
    """Proxy to Airflow to check the state of a DAG run."""
    url = (
        f"{settings.airflow_base_url}/api/v1/dags"
        f"/{settings.airflow_dag_id}/dagRuns/{dag_run_id}"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            auth=(settings.airflow_username, settings.airflow_password),
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

    return StatusResponse(dag_run_id=dag_run_id, state=data.get("state", "unknown"))
