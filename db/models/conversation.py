from datetime import datetime, timezone
from enum import Enum

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Conversation(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    id: ObjectId | None = Field(default=None, alias="_id")
    session_id: str
    user_id: str
    channel: str
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda:datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda:datetime.now(timezone.utc))

    def to_mongo(self) -> dict:
        data = self.model_dump(by_alias=True, exclude_none=True)
        return data

    @classmethod
    def from_mongo(cls, data: dict) -> "Conversation":
            return cls.model_validate(data)
    

