from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    graphdb_host: str
    graphdb_repository: str
    graphdb_username: str
    graphdb_password: str

    class Config:
        env_file = ".env"


settings = Settings()
