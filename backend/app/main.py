from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import init_db
from app.routers import api_router


def create_app() -> FastAPI:
    application = FastAPI(title="Project Management MVP")
    init_db()
    application.include_router(api_router, prefix="/api")

    app_dir = Path(__file__).parent
    frontend_static_dir = app_dir / "frontend_static"
    fallback_static_dir = app_dir / "static"
    site_dir = frontend_static_dir if frontend_static_dir.exists() else fallback_static_dir

    application.mount("/", StaticFiles(directory=site_dir, html=True), name="frontend")

    return application


app = create_app()
