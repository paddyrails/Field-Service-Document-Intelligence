from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    #OpenAI
    openai_api_key:str
    openai_chat_model:str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    #MongoDB
    mongodb_uri:str
    mongodb_db_name:str = "ritecare"

    #Microservices Urls
    bu1_base_url: str = "http://localhost:8001"
    bu2_base_url: str = "http://localhost:8002"
    bu3_base_url: str = "http://localhost:8003"
    bu4_base_url: str = "http://localhost:8004"
    bu5_base_url: str = "http://localhost:8006"
    
    #RAG
    rag_chunk_size:int = 500
    rag_chunk_overlap:int = 50
    rag_top_k: int = 5

    #Load History for conversation
    max_history_tokens: int = 3000

    #app
    log_level:str = "INFO"
    env: str = "development"

settings = Settings()

