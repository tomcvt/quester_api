
import re
from uuid import UUID

from fastapi import BackgroundTasks

from app.exceptions import ForbiddenException
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdateEvent
from app.services.notification_service import NotificationService


class UserService:
    def __init__(self, repo: UserRepository, notif_service: NotificationService):
        self.repo = repo
        self.notif_service = notif_service
    
    async def get_user_by_public_id(self, public_id: UUID):
        return await self.repo.get_user_by_public_id(public_id)
    
    async def get_user_by_id(self, id: int):
        return await self.repo.get_user_by_id(id)
    
    async def change_username(
        self, 
        current_user: User | None, 
        new_username: str,
        notify: bool = True,
        background_tasks: BackgroundTasks | None = None) -> User:
        if not current_user:
            raise ForbiddenException("You must be logged in to change your username.")
        self.validate_username(new_username)
        updatedUser = await self.repo.change_username(current_user.id, new_username)
        userUpdateEvent = UserUpdateEvent(
            id=current_user.id,
            public_id=current_user.public_id,
            type="USERNAME_CHANGED",
            data=new_username,
            updated_at=updatedUser.updated_at
        )
        if notify and background_tasks:
            background_tasks.add_task(self.notif_service.notify_user_updated, userUpdateEvent)
        if notify and not background_tasks:
            await self.notif_service.notify_user_updated(userUpdateEvent)
        return updatedUser
    
    async def change_phone_number(
        self, current_user: User | None, new_phone_number: str, notify: bool = True, background_tasks: BackgroundTasks | None = None) -> User:
        if not current_user:
            raise ForbiddenException("You must be logged in to change your phone number.")
        self.validate_phone_number(new_phone_number)
        updatedUser = await self.repo.change_phone_number(current_user.id, new_phone_number)
        userUpdateEvent = UserUpdateEvent(
            id=current_user.id,
            public_id=current_user.public_id,
            type="PHONE_NUMBER_CHANGED",
            data=new_phone_number,
            updated_at=updatedUser.updated_at
        )
        if notify and background_tasks:
            background_tasks.add_task(self.notif_service.notify_user_updated, userUpdateEvent)
        if notify and not background_tasks:
            await self.notif_service.notify_user_updated(userUpdateEvent)
        return updatedUser
    async def change_username_and_phone_number(
        self,
        current_user: User | None,
        new_username: str,
        new_phone_number: str,
        notify: bool = True,
        background_tasks: BackgroundTasks | None = None
    ) -> User:
        if not current_user:
            raise ForbiddenException("You must be logged in to change your username and phone number.")
        self.validate_username(new_username)
        self.validate_phone_number(new_phone_number)
        updatedUser = await self.repo.change_username_and_phone_number(current_user.id, new_username, new_phone_number)
        userUpdateEvent = UserUpdateEvent(
            id=current_user.id,
            public_id=current_user.public_id,
            type="USERNAME_AND_PHONE_NUMBER_CHANGED",
            data=f"{new_username}|{new_phone_number}",
            updated_at=updatedUser.updated_at
        )
        if notify and background_tasks:
            background_tasks.add_task(self.notif_service.notify_user_updated, userUpdateEvent)
        if notify and not background_tasks:
            await self.notif_service.notify_user_updated(userUpdateEvent)
        return updatedUser
    
    
    def validate_username(self, username: str):
        # regex for allowed characters: letters, numbers, underscores, and hyphens 3-20
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters long.")
        # regex for allowed characters: letters, numbers, underscores, and hyphens 3-20
        pattern = r'^[a-zA-Z0-9_-]{3,20}$'
        if not re.match(pattern, username):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens, and must be 3-20 characters long.")
    
    def validate_phone_number(self, phone_number: str):
        # regex for phone number validation (simple international format)
        pattern = r'^\+?[1-9]\d{1,14}$'
        if not re.match(pattern, phone_number):
            raise ValueError("Invalid phone number format. Must be in international format, e.g. +1234567890.")
    