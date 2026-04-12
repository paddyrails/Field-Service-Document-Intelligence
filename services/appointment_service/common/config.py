from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic: str = "appointment.booked"
    log_level: str = "INFO"
    env: str = "development"
    app_port: int = 8007


settings = Settings()
