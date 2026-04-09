

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.exceptions import UserAlreadyExistsException
from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalars().first()
    
    async def get_users_by_username(self, username: str) -> list[User]:
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return list(result.scalars().all())
    
    async def get_user_by_public_id(self, public_id: UUID) -> User | None:
        result = await self.db.execute(
            select(User).where(User.public_id == public_id)
        )
        return result.scalars().first()
    
    async def get_user_by_installation_id(self, installation_id: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.installation_id == installation_id)
        )
        return result.scalars().first()
    
    async def update_fcm_token(self, user_id: int, fcm_token: str) -> User:
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        user.fcm_token = fcm_token
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def update_session_token(self, user_id: int, session_token: str) -> User:
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        user.session_token = session_token
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def create_user(self, user: User) -> User:
        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception as e:
            await self.db.rollback()
            if "UNIQUE constraint failed: users.installation_id" in str(e):
                raise UserAlreadyExistsException("A user with this installation_id already exists.")
            raise e
    
    async def change_username(self, user_id: int, new_username: str) -> User:
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        user.username = new_username
        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except IntegrityError as e:
            await self.db.rollback()
            if "UNIQUE constraint failed: users.username" in str(e):
                raise UserAlreadyExistsException("A user with this username already exists.")
            raise e
    
    async def change_phone_number(self, user_id: int, new_phone_number: str) -> User:
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        user.phone_number = new_phone_number
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_users_by_public_ids(self, public_ids: list[UUID]) -> list[User]:
        result = await self.db.execute(
            select(User).where(User.public_id.in_(public_ids))
        )
        #return [user for user in result.scalars().all()]
        return list(result.scalars().all())