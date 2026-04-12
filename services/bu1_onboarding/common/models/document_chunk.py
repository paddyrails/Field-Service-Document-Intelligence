from datetime import datetime, timezone
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field

class DocumentChunk(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    id: ObjectId | None = Field(default=None, alias="_id")
    text: str
    embedding: list[float]
    source: str
    customer_id: str | None = None
    bu: str = "bu1"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_mongo(self) -> dict:
        return self.model_dump(by_alias=True, exclude_none=True)