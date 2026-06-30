from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class BadRequestError(AppError):
    pass


class NotFoundError(AppError):
    pass


class ConflictError(AppError):
    pass


class UnauthorizedError(AppError):
    pass


class ForbiddenError(AppError):
    pass


class UnsupportedMediaError(AppError):
    pass


class FileTooLargeError(AppError):
    pass


class UnprocessableError(AppError):
    pass


class DatabaseError(AppError):
    pass


_STATUS_MAP: dict[type[AppError], int] = {
    BadRequestError: status.HTTP_400_BAD_REQUEST,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    UnauthorizedError: status.HTTP_401_UNAUTHORIZED,
    ForbiddenError: status.HTTP_403_FORBIDDEN,
    UnsupportedMediaError: status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    FileTooLargeError: status.HTTP_413_CONTENT_TOO_LARGE,
    UnprocessableError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    status_code = _STATUS_MAP.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(status_code=status_code, content={"detail": exc.message})


def register_exception_handlers(app) -> None:
    app.add_exception_handler(AppError, app_error_handler)
