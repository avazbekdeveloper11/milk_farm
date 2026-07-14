from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    database_url: str = "sqlite+aiosqlite:///./data/oka_sut.db"
    admin_password: str = "171718"

    class Config:
        env_file = ".env"


settings = Settings()
