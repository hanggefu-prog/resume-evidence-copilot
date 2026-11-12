from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/recruitment_copilot"

    llm_provider: str = "openrouter"
    llm_model: str = "openai/gpt-oss-20b:free"
    openrouter_api_key: str = ""

    embedding_mode: str = "local"  # "local" or "fake" (fake used in tests, no model download)

    cors_origins: str = "http://localhost:3000"  # comma-separated

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def testing(self) -> bool:
        return self.app_env == "test"


settings = Settings()
