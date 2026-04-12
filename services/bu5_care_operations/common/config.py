from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    mongodb_uri: str
    mongodb_db_name: str = "ritecare"
    openai_api_key: str
    openai_embedding_model: str = "text-embedding-3-small"
    rag_top_k: int = 5

    # Kafka
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic: str = "appointment.booked"
    kafka_group_id: str = "bu5-care-operations"

    # Slack
    slack_bot_token: str
    slack_members_channel: str = "rc-care-members"

    log_level: str = "INFO"
    env: str = "development"
    app_port: int = 8006


settings = Settings()
