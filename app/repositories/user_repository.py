

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.exceptions import UserAlreadyExistsException
from app.models.user import User
from app.models.refresh_tokens import RefreshToken


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(User))
        return result.scalar_one()

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
    
    async def get_by_oauth_sub(self, oauth_sub: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.oauth_sub == oauth_sub)
        )
        return result.scalars().first()
    
    async def get_user_by_installation_id(self, installation_id: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.installation_id == installation_id)
        )
        return result.scalars().first()
    
    async def link_oauth(self, user_id: int, oauth_provider: str, oauth_sub: str, email: str | None = None) -> User:
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        user.oauth_provider = oauth_provider
        user.oauth_sub = oauth_sub
        if email:
            user.email = email
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def delete_user(self, user_id: int) -> None:
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        await self.db.delete(user)
        await self.db.commit()
    
    async def delete_user_by_installation_id(self, installation_id: str) -> None:
        user = await self.get_user_by_installation_id(installation_id)
        if not user:
            raise ValueError("User not found")
        await self.db.delete(user)
        await self.db.commit()
    
    async def update_fcm_token(self, user_id: int, fcm_token: str) -> User:
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        user.fcm_token = fcm_token
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    #TODO [AFTER] : remove, now refreh token and jwt
    async def update_session_token(self, user_id: int, session_token: str) -> User:
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        user.session_token = session_token
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def create_refresh_token(self, user_id: int, token_hash: str, family_id: UUID, expires_at: datetime) -> RefreshToken:
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at
        )
        self.db.add(refresh_token)
        await self.db.commit()
        await self.db.refresh(refresh_token)
        return refresh_token
    
    async def get_refresh_token(self, token_hash: str) -> RefreshToken | None:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalars().first()
    
    async def delete_refresh_token(self, token_id: int) -> None:
        token = await self.db.get(RefreshToken, token_id)
        if not token:
            raise ValueError("Refresh token not found")
        await self.db.delete(token)
        await self.db.commit()
    
    async def revoke_token(self, token_id: int) -> None:
        token = await self.db.get(RefreshToken, token_id)
        if not token:
            raise ValueError("Refresh token not found")
        token.revoke()
        self.db.add(token)
        await self.db.commit()
    
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
    
    async def change_username_and_phone_number(self, user_id: int, new_username: str, new_phone_number: str) -> User:
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        user.username = new_username
        user.phone_number = new_phone_number
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
    
    async def get_users_by_public_ids(self, public_ids: list[UUID]) -> list[User]:
        result = await self.db.execute(
            select(User).where(User.public_id.in_(public_ids))
        )
        return list(result.scalars().all())

    async def get_users_page(self, page: int, size: int) -> tuple[list[User], int]:
        users_result = await self.db.execute(
            select(User).order_by(User.id).limit(size).offset(page * size)
        )
        count_result = await self.get_count()
        return list(users_result.scalars().all()), count_result