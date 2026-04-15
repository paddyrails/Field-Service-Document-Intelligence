from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    mongodb_uri: str
    mongodb_db_name: str = "ritecare"
    google_api_key: str
    google_embedding_model: str = "gemini-embedding-001"
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50
    rag_top_k: int = 5
    log_level: str = "INFO"
    env: str = "development"
    app_port: int = 8004


settings = Settings()
