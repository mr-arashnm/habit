from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # تنظیمات دیتابیس و امنیت
    SECRET_KEY: str = "SUPER_SECRET_KEY"
    ALGORITHM: str = "HS256"

    # تنظیمات بازی (Game Logic)
    VOUCH_THRESHOLD: int = 3  # مقدار پیش‌فرض
    REPUTATION_REWARD: int = 10
    COIN_REWARD: int = 50
    PENALTY_OFFSET: int = -5

    class Config:
        env_file = ".env"


settings = Settings()