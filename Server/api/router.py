from fastapi import APIRouter

from api.history.routes import router as history_router
from api.upload_image.routes import router as upload_image_router
from api.upload_video.routes import router as upload_video_router
from api.users.routes import router as users_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(users_router)
api_router.include_router(upload_image_router)
api_router.include_router(upload_video_router)
api_router.include_router(history_router)

