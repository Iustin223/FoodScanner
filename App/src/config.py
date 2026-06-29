from pathlib import Path
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict



BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

MODEL_PATH = PROJECT_ROOT / "trocr-model-romanian-final"
DB_PATH = PROJECT_ROOT / "app.db"

UPLOAD_DIR =  BASE_DIR / "src" / "static" / "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

#print(f"MODEL_PATH: {MODEL_PATH}")
#print(f"MODEL exists: {MODEL_PATH.exists()}")
#print(f"DB_PATH: {DB_PATH}")
#print(f"DB exists: {DB_PATH.exists()}")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = PROJECT_ROOT / ".env",
        env_file_encoding="utf-8"
    )

    #API_V1_STR: str = "/api/v1"
    secret_key : SecretStr  
    algorithm: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES : int = 60 * 24 * 4 



settings = Settings()



