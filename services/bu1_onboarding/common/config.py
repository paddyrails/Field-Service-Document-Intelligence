from pydantic_settings import BaseSettings, SettingsConfigDict

class Setttings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    #MongoDB
    mongodb_uri: str
    mongodb_db_name: str = "ritecare"

    #OPenAI
    openai_api_key: str
    openai_embedding_model:str = "text-embedding-3-small"

    #RAG
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50
    rag_top_k: int = 5

    #App
    log_level:str = "INFO"
    env:str = "development"
    app_port:int = 8001

settings = Setttings()    