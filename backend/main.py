"""
ORCA Backend Application Entrypoint (SIH26176)
Marine Ecosystem Reasoning with Collaborative Agents
FastAPI Core Server & Multi-Agent Dispatcher Engine
"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes import api_router
from backend.api.session import session_router
from backend.api.middleware import ProcessTimeAndLoggingMiddleware, setup_cors_origins


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan setup and teardown."""
    print("==================================================================")
    print("🚀 ORCA Marine Intelligence Engine Started (SIH26176)")
    print("🌊 Role: Member 5 (Backend API & Pipeline)")
    print("📡 Endpoints: /api/v1/query | /api/v1/mock-query | /api/v1/health")
    print("🗺️ WebGIS Layers: /api/v1/layers | Multi-Turn Sessions: /api/v1/sessions")
    print("==================================================================")
    yield
    print("⏹️ ORCA Backend Shutting Down...")


app = FastAPI(
    title="Project ORCA - Marine Ecosystem Reasoning Engine",
    description=(
        "Autonomous AI-driven marine intelligence platform (SIH26176). "
        "Transforms natural language queries into explainable, evidence-backed "
        "maritime safety and fishing advisories using collaborative specialized agents."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 1. Custom Execution Timing and Logging Middleware
app.add_middleware(ProcessTimeAndLoggingMiddleware)

# 2. Cross-Origin Resource Sharing (CORS) for Member 6 Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=setup_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Include Routers
app.include_router(api_router)
app.include_router(session_router, prefix="/api/v1")


# Root / Convenience Endpoints
@app.get("/", tags=["Root"])
async def root():
    """Welcome and quick link navigation."""
    return {
        "project": "Project ORCA (SIH26176)",
        "service": "Marine Ecosystem Reasoning with Collaborative Agents",
        "role": "Member 5 - Backend API & Data Pipeline",
        "documentation": "/docs",
        "health_check": "/api/v1/health",
        "query_endpoint": "/api/v1/query",
        "mock_query_for_frontend": "/api/v1/mock-query",
        "layers_endpoint": "/api/v1/layers"
    }


@app.get("/health", tags=["Root"])
async def root_health():
    """Root level health endpoint."""
    return {"status": "healthy", "service": "ORCA Backend"}


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
