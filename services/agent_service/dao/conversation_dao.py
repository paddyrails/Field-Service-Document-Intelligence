from datetime import datetime, timezone

from db.client import get_database
from db.collections import CONVERSATIONS
from db.models.conversation import Conversation


class ConversationDao:

    @property
    def _collection(self):
        return get_database()[CONVERSATIONS]

    async def get_by_session_id(self, session_id: str) -> Conversation | None:
        doc = await self._collection.find_one({"session_id": session_id})
        if doc is None:
            return None
        return Conversation.from_mongo(doc)

    async def upsert_turn(
        self,
        session_id: str,
        channel: str,
        user_id: str,
        user_text: str,
        ai_text: str,
    ) -> None:
        now = datetime.now(timezone.utc)
        await self._collection.update_one(
            {"session_id": session_id},
            {
                "$setOnInsert": {
                    "session_id": session_id,
                    "channel": channel,
                    "user_id": user_id,
                    "created_at": now,
                },
                "$push": {
                    "messages": {
                        "$each": [
                            {"role": "user", "content": user_text, "timestamp": now},
                            {"role": "assistant", "content": ai_text, "timestamp": now},
                        ]
                    }
                },
                "$set": {"updated_at": now},
            },
            upsert=True,
        )
