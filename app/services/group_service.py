from datetime import datetime
import uuid

from loguru import logger
from app.models.group_member import MemberRole
from app.models.user import User
from app.repositories.group_member_repository import GroupMemberRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.quest_repository import QuestRepository
from app.schemas.group import CreateGroupRequest
from app.models.group import Group
from app.schemas.group_member import GroupMemberSyncDTO
from app.schemas.quest import QuestSyncDTO

class GroupService:
    def __init__(self, repo: GroupRepository, member_repo: GroupMemberRepository, quest_repo: QuestRepository):
        self.repo = repo
        self.member_repo = member_repo
        self.quest_repo = quest_repo

    async def create_group(self, current_user: User, request: CreateGroupRequest) -> Group:
        logger.info(f"Creating group with name: {request.name}")
        group = Group(
            name=request.name,
            password=request.password,
            type=request.type,
            visibility=request.visibility,
        )
        result = await self.repo.create(group)
        
        # Add the current user as a member of the newly created group
        owner = await self.member_repo.add_user_to_group_with_role(current_user, result, MemberRole.OWNER)
        
        logger.info(f"Group {result.name} created with public_id: {result.public_id}")
        logger.info(f"User {current_user.username} added as OWNER to group {result.public_id}")
        return result
    
    async def get_group_by_public_id(self, public_id: uuid.UUID) -> Group | None:
        return await self.repo.get_by_public_id(public_id)
    
    async def sync_group_members_after_timestamp(self, group_public_id: uuid.UUID, timestamp: datetime) -> list[GroupMemberSyncDTO]:
        group = await self.repo.get_by_public_id(group_public_id)
        if not group:
            logger.warning(f"Group with public_id {group_public_id} not found for syncing members.")
            return []
        
        members_data = await self.member_repo.fetch_group_members_w_details_after_timestamp(group.id, timestamp)
        return [
            GroupMemberSyncDTO(
                group_public_id=group.public_id,
                user_public_id=member.user_public_id,
                role=member.role,
                username=member.username,
                updated_at=member.updated_at
            )
            for member in members_data
        ]
    async def sync_quests_after_timestamp(self, group_public_id: uuid.UUID, timestamp: datetime) -> list[QuestSyncDTO]:
        group = await self.repo.get_by_public_id(group_public_id)
        if not group:
            logger.warning(f"Group with public_id {group_public_id} not found for syncing quests.")
            return []
        quests = await self.quest_repo.fetch_quests_by_group_id_after_timestamp(group.id, timestamp)
        return [
            QuestSyncDTO(
                public_id=quest.public_id,
                group_public_id=group.public_id,
                name=quest.name,
                data=quest.data,
                type=quest.type,
                inclusive=quest.inclusive,
                status=quest.status,
                creator_public_id=quest.creator_public_id,
                created_at=quest.created_at,
                updated_at=quest.updated_at
            )
            for quest in quests
        ]
        
