from datetime import datetime
import uuid

from fastapi import BackgroundTasks
from loguru import logger
from app.exceptions import ForbiddenException, UnauthorizedException
from app.models.group_member import MemberRole
from app.models.user import User, UserRole
from app.repositories.group_member_repository import GroupMemberRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.quest_repository import QuestRepository
from app.repositories.user_repository import UserRepository
from app.schemas.group import CreateGroupRequest
from app.models.group import Group
from app.schemas.group_member import GroupMemberSyncDTO
from app.schemas.quest import QuestSyncDTO
from app.services import notification_service
from app.services.notification_service import NotificationService

class GroupService:
    def __init__(
        self, 
        repo: GroupRepository,
        member_repo: GroupMemberRepository,
        quest_repo: QuestRepository,
        user_repo: UserRepository,
        notif_service: NotificationService,
        ):
        self.repo = repo
        self.member_repo = member_repo
        self.quest_repo = quest_repo
        self.user_repo = user_repo
        self.notif_service = notif_service

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
                description=quest.description,
                date=quest.date,
                deadline_start=quest.deadline_start,
                deadline_end=quest.deadline_end,
                address=quest.address,
                contact_number=quest.contact_number,
                contact_info=quest.contact_info,
                data=quest.data,
                type=quest.type,
                inclusive=quest.inclusive,
                status=quest.status,
                creator_public_id=quest.creator_public_id,
                created_at=quest.created_at,
                updated_at=quest.updated_at,
                accepted_by_public_id=quest.accepted_by_public_id
            )
            for quest in quests
        ]
    
    async def join_group(self, current_user: User, group_public_id: uuid.UUID) -> Group:
        group = await self.repo.get_by_public_id(group_public_id)
        if not group:
            logger.warning(f"Group with public_id {group_public_id} not found for joining.")
            raise ValueError("Group not found.")
        
        # Check if the user is already a member of the group
        is_member = await self.member_repo.is_member(current_user.id, group.id)
        if is_member:
            logger.warning(f"User {current_user.username} is already a member of group {group_public_id}.")
            return group
        
        await self.member_repo.add_user_to_group_with_role(current_user, group, MemberRole.MEMBER)
        logger.info(f"User {current_user.username} joined group {group_public_id} as MEMBER.")
        return group
    
    async def join_group_with_password(self, current_user: User, group_name: str, password: str | None, background_tasks: BackgroundTasks | None) -> Group:
        group = await self.repo.get_by_name(group_name)
        if not group:
            logger.warning(f"Group with name {group_name} not found for joining.")
            raise ValueError("Group not found.")
        
        if group.password and group.password != password:
            logger.warning(f"Incorrect password provided for joining group {group.public_id}.")
            raise ValueError("Incorrect password.")
        
        # Check if the user is already a member of the group
        is_member = await self.member_repo.is_member(current_user.id, group.id)
        if is_member:
            logger.warning(f"User {current_user.username} is already a member of group {group.public_id}.")
            return group
        
        await self.member_repo.add_user_to_group_with_role(current_user, group, MemberRole.MEMBER)
        if background_tasks:
            background_tasks.add_task(self.notif_service.notify_user_role_changed, current_user, current_user, group, MemberRole.MEMBER)
        else:
            await self.notif_service.notify_user_role_changed(current_user, current_user, group, MemberRole.MEMBER)
        logger.info(f"User {current_user.username} joined group {group.public_id} as MEMBER.")
        return group
    
    async def leave_group(self, current_user: User, group_public_id: uuid.UUID, background_tasks: BackgroundTasks | None):
        group = await self.repo.get_by_public_id(group_public_id)
        if not group:
            logger.warning(f"Group with public_id {group_public_id} not found for leaving.")
            raise ValueError("Group not found.")
        me_member = await self.member_repo.get_member(current_user.id, group.id)
        if not me_member:
            logger.warning(f"User {current_user.username} is not a member of group {group_public_id} for leaving.")
            raise ValueError("User is not a member of the group.")
        if me_member.role == MemberRole.OWNER:
            logger.warning(f"User {current_user.username} attempted to leave group {group_public_id} but is the OWNER, which is not allowed.")
            raise ValueError("Group owners cannot leave the group. Please transfer ownership or delete the group.")        
        wasDeleted = await self.member_repo.remove_user_from_group(current_user.id, group.id)
        if wasDeleted:
            logger.info(f"User {current_user.username} left group {group_public_id}.")
        else:
            logger.warning(f"User {current_user.username} was not a member of group {group_public_id}.")
            raise ValueError("User is not a member of the group.")
        if background_tasks:
            background_tasks.add_task(self.notif_service.notify_user_role_changed, current_user, current_user, group, "LEFT")
        else:
            await self.notif_service.notify_user_role_changed(current_user, current_user, group, "LEFT")
        return
    
    async def set_role_su(self, current_user: User, group_public_id: uuid.UUID, user_public_id: uuid.UUID, role: MemberRole, background_tasks: BackgroundTasks | None):
        group = await self.repo.get_by_public_id(group_public_id)
        if not group:
            logger.warning(f"Group with public_id {group_public_id} not found for setting user role.")
            raise ValueError("Group not found.")
        user_changed = await self.user_repo.get_user_by_public_id(user_public_id)
        if not user_changed:
            logger.warning(f"User with public_id {user_public_id} not found for setting role in group {group_public_id}.")
            raise ValueError("Target user not found.")
        user_member = await self.member_repo.get_member(user_changed.id, group.id)
        if not user_member:
            logger.warning(f"User {user_changed.username} is not a member of group {group_public_id} for setting role.")
            raise ValueError("Target user is not a member of the group.")
        wasUpdated = await self.member_repo.update_member_role(user_changed.id, group.id, role)
        if wasUpdated:
            logger.info(f"User {current_user.username} set role of user {user_changed.username} to {role.value} in group {group_public_id}.")
        else:
            logger.warning(f"Failed to update role for user {user_changed.username} in group {group_public_id}.")
            raise ValueError("Failed to update user role.")
        if background_tasks:
            background_tasks.add_task(self.notif_service.notify_user_role_changed, current_user, user_changed, group, role)
        else:
            await self.notif_service.notify_user_role_changed(current_user, user_changed, group, role)
    
    async def set_user_role(self, current_user: User, group_public_id: uuid.UUID, user_public_id: uuid.UUID, role: MemberRole, background_tasks: BackgroundTasks | None):
        if current_user.role == UserRole.SUPERUSER:
            await self.set_role_su(current_user, group_public_id, user_public_id, role, background_tasks)
            return
        if role == MemberRole.OWNER:
            logger.warning(f"Attempt to set user role to OWNER in group {group_public_id} which is not allowed.")
            raise ValueError("Cannot set user role to OWNER.")
        group = await self.repo.get_by_public_id(group_public_id)
        if not group:
            logger.warning(f"Group with public_id {group_public_id} not found for setting user role.")
            raise ValueError("Group not found.")
        me_member = await self.member_repo.get_member(current_user.id, group.id)
        if not me_member or me_member.role != MemberRole.OWNER:
            logger.warning(f"User {current_user.username} does not have permission to set user roles in group {group_public_id}.")
            raise ForbiddenException("You do not have permission to set user roles in this group.")
        user_changed = await self.user_repo.get_user_by_public_id(user_public_id)
        if not user_changed:
            logger.warning(f"User with public_id {user_public_id} not found for setting role in group {group_public_id}.")
            raise ValueError("Target user not found.")
        if user_changed.id == current_user.id:
            logger.warning(f"User {current_user.username} attempted to change their own role in group {group_public_id}, which is not allowed.")
            raise ValueError("You cannot change your own role.")
        user_member = await self.member_repo.get_member(user_changed.id, group.id)
        if not user_member:
            logger.warning(f"User {user_changed.username} is not a member of group {group_public_id} for setting role.")
            raise ValueError("Target user is not a member of the group.")
        wasUpdated = await self.member_repo.update_member_role(user_changed.id, group.id, role)
        if wasUpdated:
            logger.info(f"User {current_user.username} set role of user {user_changed.username} to {role.value} in group {group_public_id}.")
        else:
            logger.warning(f"Failed to update role for user {user_changed.username} in group {group_public_id}.")
            raise ValueError("Failed to update user role.")
        if background_tasks:
            background_tasks.add_task(self.notif_service.notify_user_role_changed, current_user, user_changed, group, role)
        else:
            await self.notif_service.notify_user_role_changed(current_user, user_changed, group, role)