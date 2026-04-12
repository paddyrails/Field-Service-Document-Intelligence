import os

from common.exceptions.handlers import CustomerNotFoundError, DuplicateCustomerError
from common.models.customer import Customer, KYCStatus, OnboardingStage
from common.schemas.request import CustomerCreateRequest, IngestRequest, KYCUpdateRequest
from common.schemas.response import CustomerResponse, OnBoardingStatusResponse
from dao.customer_dao import CustomerDAO
from dao.vector_dao import VectorDAO
from ingestion.pipeline import run_pipeline

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


class CustomerService:
    def __init__(self, dao: CustomerDAO, vector_dao: VectorDAO) -> None:
        self.dao = dao
        self.vector_dao = vector_dao

    async def register_customer(self, request: CustomerCreateRequest) -> CustomerResponse:
        existing = await self.dao.find_by_email(request.email)
        if existing:
            raise DuplicateCustomerError(request.email)

        customer = Customer(
            name=request.name,
            email=request.email,
            phone=request.phone,
            address=request.address,
        )
        customer_id = await self.dao.insert(customer)
        created = await self.dao.find_by_id(customer_id)
        return self._to_response(created)  # type: ignore[arg-type]

    async def get_customer(self, customer_id: str) -> CustomerResponse:
        customer = await self.dao.find_by_id(customer_id)
        if customer is None:
            raise CustomerNotFoundError(customer_id)
        return self._to_response(customer)

    async def update_kyc(self, customer_id: str, request: KYCUpdateRequest) -> CustomerResponse:
        customer = await self.dao.find_by_id(customer_id)
        if customer is None:
            raise CustomerNotFoundError(customer_id)

        await self.dao.update_kyc(customer_id, request.kyc_status, request.kyc_notes)

        if request.kyc_status == KYCStatus.APPROVED:
            await self.dao.update_onboarding_stage(customer_id, OnboardingStage.KYC_VERIFIED)

        updated = await self.dao.find_by_id(customer_id)
        return self._to_response(updated)  # type: ignore[arg-type]

    async def get_onboarding_status(self, customer_id: str) -> OnBoardingStatusResponse:
        customer = await self.dao.find_by_id(customer_id)
        if customer is None:
            raise CustomerNotFoundError(customer_id)

        return OnBoardingStatusResponse(
            customer_id=customer_id,
            onboarding_stage=customer.onboarding_stage,
            kyc_status=customer.kyc_status,
            is_complete=customer.onboarding_stage == OnboardingStage.COMPLETED,
        )

    async def ingest_folder(self, request: IngestRequest) -> dict:
        """
        Scans a mounted folder, runs the ingestion pipeline on each supported
        file, and stores all chunks via VectorDAO.
        """
        if not os.path.exists(request.folder_path):
            raise FileNotFoundError(f"Folder not found: {request.folder_path}")

        if not os.path.isdir(request.folder_path):
            raise NotADirectoryError(f"Path is not a folder: {request.folder_path}")

        files = [
            os.path.join(request.folder_path, f)
            for f in os.listdir(request.folder_path)
            if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS
        ]

        if not files:
            raise FileNotFoundError(
                f"No supported files found in {request.folder_path}"
            )

        results = []
        errors = []

        for file_path in sorted(files):
            filename = os.path.basename(file_path)
            try:
                # pipeline returns list of dicts: {text, embedding, metadata}
                documents = await run_pipeline(
                    file_path=file_path,
                    metadata={
                        "source_filename": filename,
                        "bu": "bu1",
                        **request.metadata,
                    },
                )
                count = await self.vector_dao.insert_chunks(documents)
                results.append({"file": filename, "chunks_stored": count})
            except Exception as e:
                errors.append({"file": filename, "error": str(e)})

        return {
            "folder": request.folder_path,
            "files_processed": len(results),
            "total_chunks_stored": sum(r["chunks_stored"] for r in results),
            "files": results,
            "errors": errors,
        }

    async def rag_search(self, query_vector: list[float], top_k: int, filters: dict | None) -> list[dict]:
        """
        Delegates vector search to VectorDAO.
        """
        return await self.vector_dao.search(query_vector, top_k=top_k, filters=filters)

    def _to_response(self, customer: Customer) -> CustomerResponse:
        return CustomerResponse(
            id=str(customer.id),
            name=customer.name,
            email=customer.email,
            phone=customer.phone,
            address=customer.address,
            kyc_status=customer.kyc_status,
            kyc_notes=customer.kyc_notes,
            onboarding_stage=customer.onboarding_stage,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
        )
