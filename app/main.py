from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import upload, invoices, analytics, chat, export
from app.core.config import get_settings
from app.core.constants import APP_VERSION
from app.core.logging_config import setup_logging, get_logger

settings = get_settings()

# Initialize logging based on environment
setup_logging(
    level=settings.LOG_LEVEL,
    json_format=(settings.ENVIRONMENT == "production")
)
logger = get_logger(__name__)

app = FastAPI(
    title="Invoice Intelligence API",
    description="AI-powered invoice processing with NEAR AI integration",
    version=APP_VERSION
)

# Configure CORS (Cross-Origin Resource Sharing)
# Parse allowed origins from environment configuration
allowed_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]

# Log CORS configuration for security audit
logger.info(
    "CORS configured",
    extra={
        "extra_data": {
            "allowed_origins": allowed_origins,
            "environment": settings.ENVIRONMENT
        }
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Whitelist specific origins
    allow_credentials=True,  # Allow cookies and authentication headers
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicit methods only
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],  # Explicit headers
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(invoices.router, prefix="/api", tags=["invoices"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(export.router, prefix="/api", tags=["export"])


@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Invoice Intelligence API",
        "version": APP_VERSION
    }


@app.get("/health")
def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "connected"  # TODO: Add actual DB health check
    }


@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    logger.info(
        "Application starting up",
        extra={
            "extra_data": {
                "version": APP_VERSION,
                "environment": settings.ENVIRONMENT,
                "log_level": settings.LOG_LEVEL,
            }
        }
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("Application shutting down")
