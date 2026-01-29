"""FastAPI application for Sportsbeams Pipeline."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.connection import init_db
from api.routes import prospects, contacts, activities, agents, outreach, health, imports
from api.websocket import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    init_db()
    yield
    # Shutdown (if needed)


app = FastAPI(
    title="Sportsbeams Pipeline API",
    description="Automated marketing pipeline for Sportsbeams Lighting",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(prospects.router, prefix="/api/v1/prospects", tags=["Prospects"])
app.include_router(contacts.router, prefix="/api/v1/contacts", tags=["Contacts"])
app.include_router(activities.router, prefix="/api/v1/activities", tags=["Activities"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(outreach.router, prefix="/api/v1/outreach", tags=["Outreach"])
app.include_router(imports.router, prefix="/api/v1/import", tags=["Import"])
app.include_router(ws_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Sportsbeams Pipeline API",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=8765,
        reload=True,
    )
