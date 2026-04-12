from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Airflow
    airflow_base_url: str = "http://airflow:8080"
    airflow_username: str = "admin"
    airflow_password: str = "admin"
    airflow_dag_id: str = "bu_ingestion"

    # File storage (shared volume between ingestion_service and Airflow)
    upload_dir: str = "/docs/uploads"

    # Slack incoming webhook for completion notifications
    slack_webhook_url: str = ""

    # App
    log_level: str = "INFO"
    env: str = "production"
    app_port: int = 8005


settings = Settings()
