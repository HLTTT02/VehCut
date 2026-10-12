import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.controllers.clip_controller import router as clip_router
from app.api.controllers.health_controller import router as health_router
from app.api.controllers.job_controller import router as job_router
from app.api.controllers.video_controller import router as video_router
from app.api.controllers.history_controller import router as history_router
from app.api.controllers.statistics_controller import router as statistics_router
from app.core.exceptions import AppError

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(title="AutoCut Vehicle API", version="0.1.0")
    app.include_router(health_router)
    app.include_router(video_router, prefix="/api")
    app.include_router(job_router, prefix="/api")
    app.include_router(clip_router, prefix="/api")
    app.include_router(history_router, prefix="/api")
    app.include_router(statistics_router, prefix="/api")

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, error: AppError) -> JSONResponse:
        logger.exception("Application error [%s] details=%s", error.code, error.details)
        return JSONResponse(status_code=error.status_code, content={"code": error.code, "message": error.message, "details": error.details})

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, error: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"code": "VALIDATION_FAILED", "message": "Request validation failed", "details": {"errors": error.errors()}})

    @app.exception_handler(HTTPException)
    async def http_error_handler(_: Request, error: HTTPException) -> JSONResponse:
        message = error.detail if isinstance(error.detail, str) else "HTTP request failed"
        return JSONResponse(status_code=error.status_code, content={"code": "HTTP_" + str(error.status_code), "message": message, "details": {}})

    @app.exception_handler(Exception)
    async def unexpected_error_handler(_: Request, error: Exception) -> JSONResponse:
        logger.exception("Unexpected server error")
        return JSONResponse(status_code=500, content={"code": "INTERNAL_SERVER_ERROR", "message": "Unexpected server error", "details": {}})
    return app

app = create_app()
