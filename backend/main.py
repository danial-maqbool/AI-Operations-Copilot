from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.config import settings
from backend.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="OpsPilot - AI Operations Copilot",
    description="Enterprise Operations Intelligence, Safe SQL, Business Rules, and Workflow Automation Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.api import health, data_sources, catalog, quality, queries, dataframe_analysis, metrics, rules, exceptions, anomalies

# Register routers
app.include_router(health.router, prefix="/api")
app.include_router(data_sources.router, prefix="/api")
app.include_router(catalog.router, prefix="/api")
app.include_router(quality.router, prefix="/api")
app.include_router(queries.router, prefix="/api")
app.include_router(dataframe_analysis.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(rules.router, prefix="/api")
app.include_router(exceptions.router, prefix="/api")
app.include_router(anomalies.router, prefix="/api")

# Static frontend serving when built
frontend_dist = settings.BASE_DIR / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api"):
            return None
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
