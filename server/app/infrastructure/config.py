from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")
    openai_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 30.0


settings = Settings()