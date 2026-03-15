from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
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