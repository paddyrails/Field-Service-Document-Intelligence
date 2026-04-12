from service.ingestion_orchestrator import IngestionOrchestrator


def get_orchestrator() -> IngestionOrchestrator:
    return IngestionOrchestrator()
