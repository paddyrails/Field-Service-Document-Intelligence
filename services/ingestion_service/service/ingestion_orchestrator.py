import os
from common.config import settings
import httpx

class IngestionOrchestrator:
    async def trigger(self, file_bytes: bytes, filename: str, bu: str, customer_id: str, service_type: str = "") -> dict:
        file_path = await self._save_file(file_bytes, filename, bu)
        dag_run_id = await self._trigger_dag(file_path, bu, customer_id, service_type)
        return {"dag_run_id": dag_run_id, "file_path": file_path, "status": "queued"}
    
    async def _save_file(self, file_bytes: bytes, filename: str, bu: str) -> str:
        dest_dir = os.path.join(settings.upload_dir, bu)
        os.makedirs(dest_dir, exist_ok=True)
        file_path = os.path.join(dest_dir, filename)
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        return file_path
    
    async def _trigger_dag(self, file_path: str, bu: str, customer_id: str, service_type: str = "") -> str:
        url = f"{settings.airflow_base_url}/api/v1/dags/{settings.airflow_dag_id}/dagRuns"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={"conf": {
                    "file_path": file_path,
                    "bu": bu,
                    "customer_id": customer_id,
                    "service_type": service_type,
                }},
                auth=(settings.airflow_username, settings.airflow_password),
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()["dag_run_id"]        
        

        