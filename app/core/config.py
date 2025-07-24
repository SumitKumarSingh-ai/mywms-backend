from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "a_very_secret_key_that_should_be_changed"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    GOOGLE_CLIENT_ID: str = "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"

    class Config:
        env_file = ".env"

settings = Settings()