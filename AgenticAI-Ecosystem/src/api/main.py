from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from src.core.config import settings
from src.core.logging import get_logger, setup_logging
from src.core.exceptions import AgenticAIException
from .routes import router
from .models import ErrorResponse

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Agentic AI Ecosystem API")
    logger.info(f"Configuration: model={settings.MODEL_NAME}, vector_db={settings.VECTOR_DB_TYPE}")
    yield
    logger.info("Shutting down Agentic AI Ecosystem API")


app = FastAPI(
    title="Agentic AI Ecosystem",
    description="Production-ready Multi-Agent AI system with self-correction loops and critic-researcher workflow",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.debug(f"{request.method} {request.url.path} - {process_time:.3f}s")
    return response


@app.exception_handler(AgenticAIException)
async def agentic_exception_handler(request: Request, exc: AgenticAIException):
    logger.error(f"AgenticAI exception: {exc.message}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=exc.message,
            details=exc.details
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            details={"error": str(exc)}
        ).model_dump()
    )


app.include_router(router)


@app.get("/")
async def root():
    return {
        "name": "Agentic AI Ecosystem",
        "version": "1.0.0",
        "description": "Multi-Agent AI system with self-correction loops",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "pong"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
