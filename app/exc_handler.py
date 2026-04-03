from app import exceptions
from loguru import logger

def register_exception_handlers(app):
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from app import exceptions

    @app.exception_handler(exceptions.BadRequestException)
    async def bad_request_exception_handler(request: Request, exc: exceptions.BadRequestException):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(exceptions.NotFoundException)
    async def not_found_exception_handler(request: Request, exc: exceptions.NotFoundException):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(exceptions.UnauthorizedException)
    async def unauthorized_exception_handler(request: Request, exc: exceptions.UnauthorizedException):
        return JSONResponse(status_code=401, content={"detail": str(exc)})
    
    @app.exception_handler(exceptions.GroupNameTakenException)
    async def group_name_taken_exception_handler(request: Request, exc: exceptions.GroupNameTakenException):
        return JSONResponse(status_code=409, content={"detail": str(exc)})
    
    @app.exception_handler(exceptions.UserAlreadyInGroupException)
    async def user_already_in_group_exception_handler(request: Request, exc: exceptions.UserAlreadyInGroupException):
        return JSONResponse(status_code=409, content={"detail": str(exc)})
    
    @app.exception_handler(exceptions.InvalidCredentialsException)
    async def invalid_credentials_exception_handler(request: Request, exc: exceptions.InvalidCredentialsException):
        return JSONResponse(status_code=401, content={"detail": str(exc)})
    
    @app.exception_handler(exceptions.UserAlreadyExistsException)
    async def user_already_exists_exception_handler(request: Request, exc: exceptions.UserAlreadyExistsException):
        return JSONResponse(status_code=409, content={"detail": str(exc)})
    
    @app.exception_handler(exceptions.UserNotFoundException)
    async def user_not_found_exception_handler(request: Request, exc: exceptions.UserNotFoundException):
        return JSONResponse(status_code=404, content={"detail": str(exc)})
    
    @app.exception_handler(exceptions.ForbiddenException)
    async def forbidden_exception_handler(request: Request, exc: exceptions.ForbiddenException):
        return JSONResponse(status_code=403, content={"detail": str(exc)})
    
    @app.exception_handler(ValueError)
    async def value_error_exception_handler(request: Request, exc: ValueError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})
