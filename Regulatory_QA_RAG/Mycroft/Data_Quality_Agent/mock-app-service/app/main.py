from fastapi import FastAPI

from app.api.health import router as health_router

app = FastAPI(
    title="mock-app-service",
    description="Operational backend for the data contract agent demo.",
    version="0.1.0",
)

app.include_router(health_router)
