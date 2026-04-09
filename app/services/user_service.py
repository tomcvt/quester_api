
import re
from uuid import UUID

from app.exceptions import ForbiddenException
from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo
    
    async def get_user_by_public_id(self, public_id: UUID):
        return await self.repo.get_user_by_public_id(public_id)
    
    async def get_user_by_id(self, id: int):
        return await self.repo.get_user_by_id(id)
    
    async def change_username(self, current_user: User | None, new_username: str) -> User:
        if not current_user:
            raise ForbiddenException("You must be logged in to change your username.")
        self.validate_username(new_username)
        return await self.repo.change_username(current_user.id, new_username)
    
    async def change_phone_number(self, current_user: User | None, new_phone_number: str) -> User:
        if not current_user:
            raise ForbiddenException("You must be logged in to change your phone number.")
        return await self.repo.change_phone_number(current_user.id, new_phone_number)
    
    def validate_username(self, username: str):
        # regex for allowed characters: letters, numbers, underscores, and hyphens 3-20
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters long.")
        # regex for allowed characters: letters, numbers, underscores, and hyphens 3-20
        pattern = r'^[a-zA-Z0-9_-]{3,20}$'
        if not re.match(pattern, username):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens, and must be 3-20 characters long.")
    