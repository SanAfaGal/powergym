from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)

async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": getattr(request.state, "request_id", None)
        },
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation error",
            "details": exc.errors(),
            "status_code": 422,
            "request_id": getattr(request.state, "request_id", None)
        },
    )

async def generic_exception_handler(request: Request, exc: Exception):
    import traceback
    error_detail = f"{type(exc).__name__}: {str(exc)}"
    traceback_str = ''.join(traceback.format_tb(exc.__traceback__))
    logger.error(f"Unhandled exception: {error_detail}\n{traceback_str}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": error_detail,
            "traceback": traceback_str if hasattr(request.state, "debug") else None,
            "status_code": 500,
            "request_id": getattr(request.state, "request_id", None)
        },
    )

def setup_exception_handlers(app):
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    return app
