from app import exceptions

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
