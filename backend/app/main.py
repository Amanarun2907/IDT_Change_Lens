import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.models.database import init_db
from app.api.routes import analysis, github, reports, history, settings as settings_route

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("changelens")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing ChangeLens database...")
    await init_db()
    logger.info("ChangeLens backend successfully started.")
    yield
    logger.info("Shutting down ChangeLens backend.")

app = FastAPI(
    title="ChangeLens API",
    description="Agentic AI-Powered Code Change Intelligence, Risk Assessment & Impact Analysis Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(analysis.router, prefix="/api")
app.include_router(github.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(settings_route.router, prefix="/api")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ChangeLens Platform API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled server error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
