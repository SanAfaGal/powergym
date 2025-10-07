from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware
from app.core.config import settings

class CompressionMiddleware(GZipMiddleware):
    def __init__(self, app, minimum_size: int = 1000):
        if settings.ENABLE_COMPRESSION:
            super().__init__(app, minimum_size=minimum_size)
        else:
            self.app = app
