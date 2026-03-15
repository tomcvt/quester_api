from loguru import logger
from app.repositories.group_repository import GroupRepository
from app.schemas.group import CreateGroupRequest
from app.models.group import Group

class GroupService:
    def __init__(self, repo: GroupRepository):
        self.repo = repo

    async def create_group(self, request: CreateGroupRequest) -> Group:
        logger.info(f"Creating group with name: {request.name}")
        group = Group(
            name=request.name,
            password=request.password,
            type=request.type,
            visibility=request.visibility,
        )
        result = await self.repo.create(group)
        logger.info(f"Group {result.name} created with public_id: {result.public_id}")
        return result