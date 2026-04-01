
class GroupNameTakenException(Exception):
    pass

class UserAlreadyInGroupException(Exception):
    pass

class InvalidCredentialsException(Exception):
    pass

class UserAlreadyExistsException(Exception):
    pass

class UserNotFoundException(Exception):
    pass

class BadRequestException(Exception):
    pass

class NotFoundException(Exception):
    pass

class UnauthorizedException(Exception):
    pass

class ForbiddenException(Exception):
    pass