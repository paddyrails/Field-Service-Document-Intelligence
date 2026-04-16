import json
from google.adk.sessions import BaseSessionService, Session
from motor.motor_asyncio import AsyncIOMotorDatabase
from db.client import get_database


def _sanitize(obj):
    """Recursively convert sets to lists and remove non-BSON types."""
    if isinstance(obj, set):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


class MongoSessionService(BaseSessionService):
    def __init__(self):
        self.db: AsyncIOMotorDatabase = get_database()
        self.collection = self.db["adk_sessions"]

    async def create_session(self, *, app_name, user_id, state=None, session_id=None, **kwargs) -> Session:
        session = Session(app_name=app_name, user_id=user_id, state=state or {}, id=session_id)
        await self.collection.insert_one(_sanitize(session.model_dump()))
        return session

    async def get_session(self, *, app_name: str, user_id: str, session_id: str, **kwargs) -> Session | None:
        doc = await self.collection.find_one({"id": session_id})
        if doc:
            doc.pop("_id", None)
            return Session(**doc)
        return await self.create_session(
            app_name=app_name, user_id=user_id, session_id=session_id,
        )

    async def list_sessions(self, *, app_name: str, user_id: str, **kwargs) -> list[Session]:
        sessions = []
        async for doc in self.collection.find({"app_name": app_name, "user_id": user_id}):
            doc.pop("_id", None)
            sessions.append(Session(**doc))
        return sessions

    async def delete_session(self, *, app_name: str, user_id: str, session_id: str, **kwargs) -> None:
        await self.collection.delete_one({"id": session_id})

    async def append_event(self, session: Session, event, **kwargs) -> None:
        session.events.append(event)
        event_data = _sanitize(event.model_dump())
        state_data = _sanitize(session.state)
        await self.collection.update_one(
            {"id": session.id},
            {"$push": {"events": event_data}, "$set": {"state": state_data}},
        )
