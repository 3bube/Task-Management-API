# settings.py
# This file is used to manage application settings and configurations.

from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017/task_management")


settings = Settings()

# For easy import in other modules
MONGO_URI = settings.MONGODB_URL