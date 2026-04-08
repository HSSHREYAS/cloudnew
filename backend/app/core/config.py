from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart Cloud Cost Estimator & Optimization Advisor"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173"
    aws_pricing_region: str = "us-east-1"
    aws_retry_max_attempts: int = 3
    aws_connect_timeout_seconds: int = 2
    aws_read_timeout_seconds: int = 5
    aws_spot_history_hours: int = 6
    aws_max_price_pages: int = 5
    default_compare_candidate_regions: str = "us-east-1,us-west-2,eu-west-1"
    firebase_project_id: str | None = None
    firebase_credentials_path: str | None = None
    firebase_app_name: str = "smart-cloud-cost-estimator"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def candidate_regions(self) -> list[str]:
        return [
            region.strip()
            for region in self.default_compare_candidate_regions.split(",")
            if region.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()

