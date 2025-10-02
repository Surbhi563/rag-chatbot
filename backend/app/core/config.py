"""Application configuration using Pydantic Settings."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # App metadata
    app_name: str = Field(default="rag-chatbot", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")

    # Environment
    env: str = Field(default="dev", description="Environment: dev|prod")
    port: int = Field(default=8080, description="Server port")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json|text)")

    # LLM
    llm_base_url: Optional[str] = Field(default=None)
    llm_api_key: Optional[str] = Field(default=None)
    llm_api_gw_key: Optional[str] = Field(default=None)
    llm_auth_header: Optional[str] = Field(default=None)

    # Storage
    gcs_bucket: Optional[str] = Field(default=None)
    local_bucket_dir: str = Field(default="/tmp/rag-documents")
    
    # Vector Database
    vector_db_path: Optional[str] = Field(default="/tmp/chroma_db", description="Path to ChromaDB storage")

    # Defaults
    max_children_default: int = Field(default=8)

    # Optional LLM defaults (used for future tuning/pass-through)
    llm_default_model: Optional[str] = Field(default=None)
    llm_default_provider: Optional[str] = Field(default=None)
    llm_default_temperature: Optional[float] = Field(default=None)
    llm_default_max_tokens: Optional[int] = Field(default=None)

    @property
    def is_dev(self) -> bool:
        return (self.env or "dev").lower() == "dev"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
