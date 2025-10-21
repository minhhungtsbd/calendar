from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import create_tables
from app.routes import calendar_router, notes_router, notifications_router
from app.routes.auth import router as auth_router

from app.routes.legal import router as legal_router
from app.routes.settings import router as settings_router
from app.logging_config import setup_logging, get_logger

# Setup logging configuration
setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Lịch Âm Dương",
    description="Ứng dụng lịch âm dương với ghi chú và thông báo tự động",
    version="1.0.0",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(auth_router, tags=["auth"])

app.include_router(legal_router, tags=["legal"])
app.include_router(calendar_router, tags=["calendar"])
app.include_router(notes_router, tags=["notes"])
app.include_router(notifications_router, tags=["notifications"])
app.include_router(settings_router, tags=["settings"])

# Templates
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
async def startup_event():
    """Initialize database and other startup tasks"""
    try:
        # Create database tables
        create_tables()
        logger.info("Database tables created successfully")
        
        # Log configuration (concise)
        logger.info(f"🚀 App started ({'DEBUG' if settings.debug else 'PROD'})")
        logger.info(f"📱 Telegram: {'✅' if settings.telegram_bot_token else '❌'}")
        logger.info(f"📧 Email: {'✅' if settings.smtp_username else '❌'}")
        logger.info(f"📅 Google: {'✅' if settings.google_api_key else '❌'}")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup tasks on shutdown"""
    logger.info("Application shutting down...")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": "connected",
        "redis": "connected" if settings.redis_url else "not configured"
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 page"""
    return templates.TemplateResponse(
        "404.html", 
        {"request": request}, 
        status_code=404
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Custom 500 page"""
    logger.error(f"Internal server error: {exc}")
    return templates.TemplateResponse(
        "500.html", 
        {"request": request}, 
        status_code=500
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="warning",  # Reduce uvicorn logs
        access_log=settings.debug  # Only show access logs in debug mode
    )
