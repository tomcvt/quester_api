from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.core.database import get_db
from app.repositories.group_repository import GroupRepository
from app.services.group_service import GroupService

def get_group_repository(db: AsyncSession = Depends(get_db)) -> GroupRepository:
    return GroupRepository(db)

def get_group_service(repo: GroupRepository = Depends(get_group_repository)) -> GroupService:
    return GroupService(repo)