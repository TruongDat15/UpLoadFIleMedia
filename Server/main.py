from fastapi import FastAPI
from contextlib import asynccontextmanager

# Relative imports (works from anywhere)
from core.database import Base
from core.database import engine
from core.middleware import setup_middlewares
from api import api_router

from models.user_model import User  # noqa: F401 - imported so SQLAlchemy registers metadata
from models.media_model import Media  # noqa: F401 - imported so SQLAlchemy registers metadata


# ============================================
# Startup & Shutdown Events
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database ready!")
    yield
    # Shutdown
    print("🛑 Shutting down...")


# ============================================
# Initialize FastAPI App
# ============================================
app = FastAPI(
    title="Media Upload API",
    version="1.0.0",
    description="Upload media files with chunking and processing",
    lifespan=lifespan
)

app.include_router(api_router)
setup_middlewares(app)


# ============================================
# API Endpoints
# ============================================
@app.get("/")
def root():
    return {
        "message": "Media Upload API Running",
        "docs": "http://localhost:8000/docs",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Media Upload API"
    }


