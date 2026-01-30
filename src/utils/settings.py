#  Copyright (c) 2025.
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8001
    title: str = "BPMN-CPI Simulator API"
    version: str = "1.0.0"
    docs_url: str = "/docs/"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SIMULATOR_API_",
        extra="ignore",
    )


settings = APISettings()
