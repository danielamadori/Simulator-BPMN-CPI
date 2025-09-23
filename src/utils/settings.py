#  Copyright (c) 2025.
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    host: str = Field(alias="simulator_api_host", default="127.0.0.1")
    port: int = Field(alias="simulator_api_port", default=8001)
    title: str = Field(alias="simulator_api_title", default="BPMN-CPI Simulator API")
    version: str = Field(alias="simulator_api_version", default="1.0.0")
    docs_url: str = Field(alias="simulator_api_docs_url", default="/docs/")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = APISettings()