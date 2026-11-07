from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title="VIGILANT - AI CCTV Surveillance Intelligence System",
    description="Enterprise Authentication, RBAC, and AI CCTV Stream Management Services",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/api/v1/health", tags=["System Health"])
async def health_check():
    return {
        "status": "ONLINE",
        "system": "VIGILANT AI CCTV Intelligence",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "VIGILANT AI CCTV Monitoring Intelligence API is operational",
        "docs": "/docs"
    }

