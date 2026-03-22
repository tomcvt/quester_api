

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