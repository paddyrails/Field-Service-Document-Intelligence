from dao.conversation_dao import ConversationDao
from service.conversation_service import ConversationService


def get_conversation_service() -> ConversationService:
    return ConversationService(ConversationDao())
