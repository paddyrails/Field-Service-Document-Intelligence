from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, trim_messages
from langchain_openai import ChatOpenAI

from dao.conversation_dao import ConversationDao
from shared.config import settings

from dao.conversation_dao import ConversationDao

_llm = ChatOpenAI(model=settings.openai_chat_model, api_key=settings.openai_api_key)

class ConversationService:

    def __init__(self, dao: ConversationDao):
        self._dao = dao

    async def load_history(self, session_id: str) -> list[BaseMessage]:
        """Loads prior conversation turns from MongoDB as LangChain messages."""
        conversation = await self._dao.get_by_session_id(session_id)
        if conversation is None:
            return []
        messages: list[BaseMessage] = []
        for msg in conversation.messages:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))
        return trim_messages(
            messages,
            max_tokens=settings.max_history_tokens,
            strategy="last",
            token_counter=_llm,
            start_on="human"
        )

    async def save_turn(
        self,
        session_id: str,
        channel: str,
        user_id: str,
        user_text: str,
        ai_text: str,
    ) -> None:
        """Persists a user + assistant turn to MongoDB."""
        await self._dao.upsert_turn(session_id, channel, user_id, user_text, ai_text)
