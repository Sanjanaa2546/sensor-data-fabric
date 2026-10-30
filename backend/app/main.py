from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.database import db_manager
from app.ingestion.seed_data import seed_database
from app.routers import sensors, query, anomalies, chat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure schema and seed initial sensor telemetry
    logger.info("Initializing Sensor Data Fabric...")
    seed_database()
    logger.info("Sensor Data Fabric ready for queries.")
    yield
    logger.info("Shutting down Sensor Data Fabric.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="IoT Sensor Data Fabric with SQL AST Guardrails, Time-Series Analytics, and AI Tool Calling",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(sensors.router)
app.include_router(query.router)
app.include_router(anomalies.router)
app.include_router(chat.router)

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

# Serve frontend build if present (for single-container AWS App Runner / Docker deploy)
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    logger.info(f"Serving compiled frontend static build from {frontend_dist}")
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
    @app.get("/", tags=["Root"])
    def root():
        return {
            "message": "Welcome to Sensor Data Fabric API",
            "docs_url": "/docs",
            "health": "/health"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
