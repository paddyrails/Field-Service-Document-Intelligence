from google.adk.sessions import BaseSessionService, Session
from motor.motor_asyncio import AsyncIOMotorDatabase
from db.client import get_database


class MongoSessionService(BaseSessionService):
    def __init__(self):
        self.db: AsyncIOMotorDatabase = get_database()
        self.collection = self.db["adk_sessions"]

    async def create_session(self, *, app_name, user_id, state=None, session_id=None) -> Session:
        session = Session(app_name=app_name, user_id=user_id, state=state or {}, id=session_id)
        await self.collection.insert_one(session.model_dump())
        return session

    async def get_session(self, *, app_name: str, user_id: str, session_id: str) -> Session | None:
        doc = await self.collection.find_one({"id": session_id})
        if doc:
            return Session(**doc)
        return None

    async def list_sessions(self, *, app_name: str, user_id: str) -> list[Session]:
        sessions = []
        async for doc in self.collection.find({"app_name": app_name, "user_id": user_id}):
            sessions.append(Session(**doc))
        return sessions

    async def delete_session(self, *, app_name: str, user_id: str, session_id: str) -> None:
        await self.collection.delete_one({"id": session_id})

    async def append_event(self, session: Session, event) -> None:
        session.events.append(event)
        await self.collection.update_one(
            {"id": session.id},
            {"$push": {"events": event.model_dump()}, "$set": {"state": session.state}},
        )
