from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.settings import get_settings


def setup_middlewares(app: FastAPI) -> None:
    settings = get_settings()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_method_list,
        allow_headers=settings.cors_header_list,
    )

