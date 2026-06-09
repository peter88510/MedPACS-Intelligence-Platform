from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    UPLOAD_STORAGE_PATH: str = "./storage"
    DATABASE_URL: str

    class Config:
        env_file = ".env"


settings = Settings()
