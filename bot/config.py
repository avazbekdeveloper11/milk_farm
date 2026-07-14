from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/milk_farm"
    admin_password: str = "171718"

    class Config:
        env_file = ".env"


settings = Settings()
