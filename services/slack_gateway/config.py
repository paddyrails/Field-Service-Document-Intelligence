from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    slack_bot_token: str
    slack_app_token: str
    agent_base_url: str = "http://agent:8000"
    bu5_base_url: str = "http://bu5_care_operations:8006"
    log_level: str = "INFO"


settings = Settings()
