from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    graphdb_host: str
    graphdb_repository: str
    graphdb_username: str
    graphdb_password: str

    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"

    class Config:
        env_file = ".env"


settings = Settings()
