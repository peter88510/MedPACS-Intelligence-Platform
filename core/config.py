from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    UPLOAD_STORAGE_PATH: str = "./storage"
    DATABASE_URL: str
    # 啟動時預載 AI 模型，消除第一個 /ai/segment 冷啟（見 README Step 7）。
    # 只在這次啟動要跑 AI 時設 true；預設 false（測試 / 純後端啟動零延遲）。
    AI_WARMUP_ON_STARTUP: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
