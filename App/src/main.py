from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
from config import BASE_DIR, UPLOAD_DIR
from router import router          # ADD THIS
from auth.router import router as auth_router
from auth.database import create_db

os.makedirs(str(UPLOAD_DIR), exist_ok=True)

app = FastAPI(title="Scanner Food Ingredients")

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "src" / "static")),
    name="static"
)

app.include_router(router)             # ADD THIS
app.include_router(auth_router)

@app.on_event("startup")
def startup():
    create_db()