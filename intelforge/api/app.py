from fastapi import FastAPI
from .routes.catalog import router as catalog_router
from .routes.jobs import router as jobs_router

def create_app() -> FastAPI:
    app = FastAPI(title="IntelForge API", version="0.2.0")
    app.include_router(catalog_router)
    app.include_router(jobs_router)
    return app

app = create_app()
