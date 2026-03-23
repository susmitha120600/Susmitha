from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
import time
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import BaseAPIException
from app.models.schemas import HealthResponse, ErrorResponse
from app.api import ingestion, query, evaluation

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
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
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    logger.info(
        f"Request started",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else None
    )
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    logger.info(
        f"Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time=f"{process_time:.3f}s"
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


@app.exception_handler(BaseAPIException)
async def custom_exception_handler(request: Request, exc: BaseAPIException):
    logger.error(
        f"API Exception",
        error=exc.message,
        status_code=exc.status_code,
        details=exc.details
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=exc.message,
            details=exc.details
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception",
        error=str(exc),
        exception_type=type(exc).__name__
    )
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            details=str(exc) if settings.LOG_LEVEL == "DEBUG" else None
        ).dict()
    )


app.include_router(
    ingestion.router,
    prefix="/api/v1",
    tags=["Ingestion"]
)

app.include_router(
    query.router,
    prefix="/api/v1",
    tags=["Query"]
)

app.include_router(
    evaluation.router,
    prefix="/api/v1",
    tags=["Evaluation"]
)


@app.get("/", response_model=dict)
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        from app.services.vector_store import VectorStore
        from app.services.bm25_service import BM25Service
        
        services_status = {
            "api": True,
            "vector_store": False,
            "bm25_index": False,
            "openai": False
        }
        
        try:
            vector_store = VectorStore()
            await vector_store.get_stats()
            services_status["vector_store"] = True
        except:
            pass
        
        try:
            bm25_service = BM25Service()
            bm25_service.get_stats()
            services_status["bm25_index"] = True
        except:
            pass
        
        try:
            from app.services.embedding_service import EmbeddingService
            embedding_service = EmbeddingService()
            services_status["openai"] = True
        except:
            pass
        
        overall_status = "healthy" if all(services_status.values()) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            version=settings.VERSION,
            services=services_status
        )
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            version=settings.VERSION,
            services={"api": False}
        )


if settings.ENABLE_METRICS:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


@app.on_event("startup")
async def startup_event():
    logger.info(
        f"Starting {settings.PROJECT_NAME}",
        version=settings.VERSION,
        environment=settings.PINECONE_ENVIRONMENT
    )


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        workers=settings.API_WORKERS if not settings.API_RELOAD else 1
    )
