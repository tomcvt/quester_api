import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.models.group import Group
from app.exceptions import GroupNameTakenException

class GroupRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, group: Group) -> Group:
        try:
            self.db.add(group)
            await self.db.commit()
            await self.db.refresh(group)
            return group
        except IntegrityError:
            await self.db.rollback()
            raise GroupNameTakenException(f"'{group.name}' is already taken.")
    
    async def get_by_id(self, group_id: int) -> Group | None:
        result = await self.db.execute(
            select(Group).where(Group.id == group_id)
        )
        return result.scalars().first()
    
    async def get_by_public_id(self, public_id: uuid.UUID) -> Group | None:
        result = await self.db.execute(
            select(Group).where(Group.public_id == public_id)
        )
        return result.scalars().first()
        