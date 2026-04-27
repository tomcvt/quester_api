
"""
Legacy quest service retained during product-model refactor.

from datetime import datetime
from typing import cast
import uuid

from loguru import logger
from fastapi import BackgroundTasks
from sqlalchemy import CursorResult, Result, update
from sqlalchemy.exc import IntegrityError
from app.exceptions import BadRequestException, UnauthorizedException
from app.models.group_member import MemberRole
from app.models.user import User
from app.models.quest import Quest, NewQuest, QuestStatus, UpdateQuest
from app.repositories.group_member_repository import GroupMemberRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.quest_repository import QuestRepository
from app.schemas.quest import CreateQuestRequest, QuestSyncDTO, QuestUpdateEvent
from app.services.notification_service import NotificationService


class QuestService:
    '''
    Service layer for handling quest-related operations. Quests are tasks or objectives that can be created within groups.
    Quest is an inside name, product name is Task. We keep quest internally to avoid confusion with already used task
    '''
    def __init__(
        self, 
        repo: QuestRepository, 
        group_repo: GroupRepository, 
        group_member_repo: GroupMemberRepository,
        notification_service: NotificationService
        ):
        self.repo = repo
        self.group_repo = group_repo
        self.group_member_repo = group_member_repo
        self.notification_service = notification_service
    
    async def get_quest_dto_by_public_id(self, public_id: uuid.UUID) -> QuestSyncDTO | None:
        return await self.repo.get_quest_dto_by_public_id(public_id)

    async def get_quests_page(
        self,
        page: int,
        size: int,
        status: QuestStatus | None = None,
        group_id: int | None = None,
        creator_id: int | None = None,
        name: str | None = None,
    ) -> tuple[list[Quest], int]:
        return await self.repo.get_quests_page(page, size, status, group_id, creator_id, name)
    
    async def create_quest(
        self, 
        current_user: User, 
        quest_data: NewQuest, 
        background_tasks: BackgroundTasks | None = None,
        group_public_id: uuid.UUID | None = None
        ) -> Quest:
        if not current_user:
            raise BadRequestException("Not authenticated.")
        #TODO - check if user is a member of the group before allowing quest creation
        is_member = await self.group_member_repo.is_member(current_user.id, quest_data.group_id)
        if not is_member:
            raise BadRequestException("User must be a member of the group to create a task.")
        #TODO validatiion
        
        if not group_public_id:
            group = await self.group_repo.get_by_id(quest_data.group_id)
            if not group:
                raise Exception(f"Group with id {quest_data.group_id} not found when creating quest.")
            group_public_id = group.public_id
        newQuest: Quest | None = None
        try:
            newQuest = await self.repo.create(quest_data)
        except IntegrityError:
            #TODO - this is a very generic exception handling, we should handle specific cases like unique constraint violation on quest name within the same group and return proper error messages.
            await self.repo.db.rollback()
            raise
        if not newQuest:
            raise Exception("Failed to create quest.")
        logger.info(f"Quest created: {newQuest}")
        questEvent = QuestUpdateEvent(
            id=newQuest.id,
            public_id=newQuest.public_id,
            group_id=newQuest.group_id,
            group_public_id=group_public_id,
            status=newQuest.status,
            updated_at=newQuest.updated_at
        )
        if background_tasks:
            background_tasks.add_task(
                self.notification_service.notify_group_members_of_new_quest, questEvent
            )
        else:
            await self.notification_service.notify_group_members_of_new_quest(questEvent)
        #TODO remove this debug phantom test quest if it works
        if current_user.username != "testuser1":
            from app.dev.dev_data_seeder import DevDataSeeder
            seeder = DevDataSeeder(db=self.repo.db)
            await seeder.create_quest_test_1()
        return newQuest
    
    async def create_quest_from_request(
        self, 
        current_user: User, 
        quest_request: CreateQuestRequest, 
        background_tasks: BackgroundTasks,
        ) -> Quest:
        group_id = await self.group_repo.get_group_id_by_public_id(quest_request.group_public_id)
        if not group_id:
            raise BadRequestException(f"Group with public_id {quest_request.group_public_id} not found.")
        newQuest = NewQuest(
            group_id=group_id,
            name=quest_request.name,
            description=quest_request.description,
            date=quest_request.date,
            deadline_start=quest_request.deadline_start,
            deadline_end=quest_request.deadline_end,
            address=quest_request.address,
            contact_number=quest_request.contact_number,
            contact_info=quest_request.contact_info,
            data=quest_request.data,
            type=quest_request.type,
            inclusive=quest_request.inclusive,
            status=quest_request.status,
            creator_id=current_user.id
        )
        return await self.create_quest(current_user, newQuest, background_tasks, group_public_id=quest_request.group_public_id)
    
    async def complete_quest(self, current_user: User | None, quest_public_id: uuid.UUID, background_tasks: BackgroundTasks) -> Quest:
        quest = await self.repo.get_by_public_id(quest_public_id)
        if not quest:
            raise BadRequestException("Quest not found.")
        if not current_user:
            raise UnauthorizedException("Not authenticated.")
        if quest.accepted_by_id != current_user.id:
            raise BadRequestException("User must be the one who accepted the task to complete it.")
        group = await self.group_repo.get_by_id(quest.group_id)
        if not group:
            raise BadRequestException("Group not found for the quest.")
        is_member = await self.group_member_repo.is_member(current_user.id, group.id)
        if not is_member:
            raise BadRequestException("User must be a member of the group to complete a task.")
        try:
            completed = await self.repo.complete_quest(quest.id, current_user.id)
            if not completed:
                raise BadRequestException("Failed to complete quest. It may have already been completed or its status may have changed.")
            else:
                logger.info(f"Quest completed: {quest_public_id} by user {current_user.public_id}")
        except IntegrityError:
            raise
        updated_quest = await self.repo.get_by_public_id(quest_public_id)
        if not updated_quest:
            raise Exception("Failed to retrieve updated quest after completing.")
        questEvent = QuestUpdateEvent(
            id=updated_quest.id,
            public_id=updated_quest.public_id,
            group_id=updated_quest.group_id,
            group_public_id=group.public_id,
            status=updated_quest.status,
            updated_at=updated_quest.updated_at,
            accepted_by_public_id=current_user.public_id,
            source_user_public_id=current_user.public_id
        )
        background_tasks.add_task(
            self.notification_service.notify_creator_of_completed_quest, questEvent
        )
        return updated_quest
    
    async def accept_quest(self, current_user: User | None, quest_public_id: uuid.UUID, background_tasks: BackgroundTasks) -> Quest:
        quest = await self.repo.get_by_public_id(quest_public_id)
        if not quest:
            raise BadRequestException("Quest not found.")
        if not current_user:
            raise UnauthorizedException("Not authenticated.")
        if quest.accepted_by_id:
            raise BadRequestException("Quest already accepted.")
        group_id = quest.group_id
        group = await self.group_repo.get_by_id(group_id)
        if not group:
            raise BadRequestException("Group not found for the quest.")
        is_member = await self.group_member_repo.is_member(current_user.id, group_id)
        if not is_member:
            raise BadRequestException("User must be a member of the group to accept a task.")
        try:
            accepted = await self.repo.accept_quest(quest.id, current_user.id)
            if not accepted:
                raise BadRequestException("Failed to accept quest. It may have already been accepted by someone else or its status may have changed.")
            else:
                logger.info(f"Quest accepted: {quest_public_id} by user {current_user.public_id}")
        except IntegrityError:
            raise
        updated_quest = await self.repo.get_by_public_id(quest_public_id)
        if not updated_quest:
            raise Exception("Failed to retrieve updated quest after accepting.")
        logger.info(f"Current user {current_user.public_id} accepted quest {quest_public_id}. Updated quest status: {updated_quest.status}")
        logger.info(f"user id {current_user.id} updated quest accepted_by_id to {updated_quest.accepted_by_id}")
        questEvent = QuestUpdateEvent(
            id=updated_quest.id,
            public_id=updated_quest.public_id,
            group_id=updated_quest.group_id,
            group_public_id=group.public_id,
            status=updated_quest.status,
            updated_at=updated_quest.updated_at,
            accepted_by_public_id=current_user.public_id,
            source_user_public_id=current_user.public_id
        )
        if background_tasks:
            background_tasks.add_task(
                self.notification_service.notify_group_members_of_taken_quest, questEvent
            )
        else:
            await self.notification_service.notify_group_members_of_taken_quest(questEvent)
        return updated_quest
    
    async def delete_quest_by_public_id(self, current_user: User | None, quest_public_id: uuid.UUID, background_tasks: BackgroundTasks):
        quest = await self.repo.get_by_public_id(quest_public_id)
        if not quest:
            raise BadRequestException(f"Quest not found.")
        if not current_user:
            raise UnauthorizedException("Not authenticated.")
        group = await self.group_repo.get_by_id(quest.group_id)
        if not group:
            raise BadRequestException("Group not found for the quest.")
        current_member = await self.group_member_repo.get_member(current_user.id, quest.group_id)
        if not current_member:
            raise BadRequestException("User must be a member of the group to delete a task.")
        #we need to fetch accepter, maybe later we optimize with full join projection
        accepted_by = await self.repo.get_quest_dto_by_public_id(quest_public_id)
        
        
        if quest.creator_id != current_user.id and current_member.role != MemberRole.ADMIN and current_member.role != MemberRole.OWNER:
            raise BadRequestException("You are not authorized to delete this task. Only the creator, group admins or owners can delete a task.")
        await self.repo.delete(quest.id)
        logger.info(f"Quest deleted: {quest_public_id} by user {current_user.public_id}")
        questEvent = QuestUpdateEvent(
            id=quest.id,
            public_id=quest.public_id,
            group_id=quest.group_id,
            group_public_id=group.public_id,
            status=QuestStatus.DELETED,
            updated_at=datetime.now(),
            accepted_by_public_id=accepted_by.accepted_by_public_id if accepted_by else None,
            source_user_public_id=current_user.public_id
        )
        background_tasks.add_task(
            self.notification_service.notify_group_members_of_deleted_quest, questEvent
        )
"""

from datetime import datetime
import uuid

from fastapi import BackgroundTasks
from loguru import logger
from sqlalchemy.exc import IntegrityError

from app.exceptions import BadRequestException, UnauthorizedException
from app.models.group_member import MemberRole
from app.models.quest import NewQuest, Quest, QuestStatus
from app.models.user import User
from app.repositories.group_member_repository import GroupMemberRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.quest_repository import QuestRepository
from app.schemas.quest import CreateQuestRequest, QuestSyncDTO, QuestUpdateEvent
from app.services.notification_service import NotificationService


class QuestService:
    def __init__(
        self,
        repo: QuestRepository,
        group_repo: GroupRepository,
        group_member_repo: GroupMemberRepository,
        notification_service: NotificationService,
    ):
        self.repo = repo
        self.group_repo = group_repo
        self.group_member_repo = group_member_repo
        self.notification_service = notification_service

    async def get_quest_dto_by_public_id(self, public_id: uuid.UUID) -> QuestSyncDTO | None:
        return await self.repo.get_quest_dto_by_public_id(public_id)

    async def get_quests_page(
        self,
        page: int,
        size: int,
        status: QuestStatus | None = None,
        group_id: int | None = None,
        creator_id: int | None = None,
        name: str | None = None,
    ) -> tuple[list[Quest], int]:
        return await self.repo.get_quests_page(page, size, status, group_id, creator_id, name)

    async def create_quest(
        self,
        current_user: User,
        quest_data: NewQuest,
        background_tasks: BackgroundTasks | None = None,
        group_public_id: uuid.UUID | None = None,
    ) -> Quest:
        if not current_user:
            raise BadRequestException("Not authenticated.")
        is_member = await self.group_member_repo.is_member(current_user.id, quest_data.group_id)
        if not is_member:
            raise BadRequestException("User must be a member of the group to create a task.")

        if not group_public_id:
            group = await self.group_repo.get_by_id(quest_data.group_id)
            if not group:
                raise Exception(f"Group with id {quest_data.group_id} not found when creating quest.")
            group_public_id = group.public_id

        try:
            new_quest = await self.repo.create(quest_data)
        except IntegrityError:
            await self.repo.db.rollback()
            raise

        logger.info(f"Quest created: {new_quest}")
        quest_event = QuestUpdateEvent(
            id=new_quest.id,
            public_id=new_quest.public_id,
            group_id=new_quest.group_id,
            group_public_id=group_public_id,
            status=new_quest.status,
            updated_at=new_quest.updated_at,
        )
        if background_tasks:
            background_tasks.add_task(self.notification_service.notify_group_members_of_new_quest, quest_event)
        else:
            await self.notification_service.notify_group_members_of_new_quest(quest_event)
        # TODO [PENDING]: delayed-start quests currently emit a new-quest notification at creation time.
        # When the start-time queue is added, notification timing may need to move to the OPEN transition.

        if current_user.username != "testuser1":
            from app.dev.dev_data_seeder import DevDataSeeder

            seeder = DevDataSeeder(db=self.repo.db)
            await seeder.create_quest_test_1()
        return new_quest

    async def create_quest_from_request(
        self,
        current_user: User,
        quest_request: CreateQuestRequest,
        background_tasks: BackgroundTasks,
    ) -> Quest:
        group_id = await self.group_repo.get_group_id_by_public_id(quest_request.group_public_id)
        if not group_id:
            raise BadRequestException(f"Group with public_id {quest_request.group_public_id} not found.")
        if quest_request.start_time is not None and quest_request.status != QuestStatus.CREATED:
            raise BadRequestException("Quest with start_time must be created with status CREATED.")
        if quest_request.status == QuestStatus.CREATED and quest_request.start_time is None:
            raise BadRequestException("Quest with status CREATED must provide start_time.")
        if quest_request.start_time is not None and quest_request.start_time <= datetime.utcnow():
            raise BadRequestException("Quest start_time must be in the future.")

        new_quest = NewQuest(
            group_id=group_id,
            name=quest_request.name,
            description=quest_request.description,
            start_time=quest_request.start_time,
            deadline=quest_request.deadline,
            address=quest_request.address,
            data=quest_request.data,
            reward_type=quest_request.reward_type,
            reward_value=quest_request.reward_value,
            inclusive=quest_request.inclusive,
            status=quest_request.status,
            creator_id=current_user.id,
        )
        return await self.create_quest(current_user, new_quest, background_tasks, group_public_id=quest_request.group_public_id)

    async def complete_quest(self, current_user: User | None, quest_public_id: uuid.UUID, background_tasks: BackgroundTasks) -> Quest:
        quest = await self.repo.get_by_public_id(quest_public_id)
        if not quest:
            raise BadRequestException("Quest not found.")
        if not current_user:
            raise UnauthorizedException("Not authenticated.")
        if quest.accepted_by_id != current_user.id:
            raise BadRequestException("User must be the one who accepted the task to complete it.")

        group = await self.group_repo.get_by_id(quest.group_id)
        if not group:
            raise BadRequestException("Group not found for the quest.")
        is_member = await self.group_member_repo.is_member(current_user.id, group.id)
        if not is_member:
            raise BadRequestException("User must be a member of the group to complete a task.")

        try:
            completed = await self.repo.complete_quest(quest.id, current_user.id)
            if not completed:
                raise BadRequestException("Failed to complete quest. It may have already been completed or its status may have changed.")
            logger.info(f"Quest completed: {quest_public_id} by user {current_user.public_id}")
        except IntegrityError:
            raise

        updated_quest = await self.repo.get_by_public_id(quest_public_id)
        if not updated_quest:
            raise Exception("Failed to retrieve updated quest after completing.")
        quest_event = QuestUpdateEvent(
            id=updated_quest.id,
            public_id=updated_quest.public_id,
            group_id=updated_quest.group_id,
            group_public_id=group.public_id,
            status=updated_quest.status,
            updated_at=updated_quest.updated_at,
            accepted_by_public_id=current_user.public_id,
            source_user_public_id=current_user.public_id,
        )
        background_tasks.add_task(self.notification_service.notify_creator_of_completed_quest, quest_event)
        return updated_quest

    async def accept_quest(self, current_user: User | None, quest_public_id: uuid.UUID, background_tasks: BackgroundTasks) -> Quest:
        quest = await self.repo.get_by_public_id(quest_public_id)
        if not quest:
            raise BadRequestException("Quest not found.")
        if not current_user:
            raise UnauthorizedException("Not authenticated.")
        if quest.accepted_by_id:
            raise BadRequestException("Quest already accepted.")
        if quest.status != QuestStatus.OPEN:
            raise BadRequestException("Only open quests can be accepted.")
        if quest.creator_id == current_user.id and not quest.inclusive:
            raise BadRequestException("Creator cannot accept a non-inclusive quest.")

        group = await self.group_repo.get_by_id(quest.group_id)
        if not group:
            raise BadRequestException("Group not found for the quest.")
        is_member = await self.group_member_repo.is_member(current_user.id, quest.group_id)
        if not is_member:
            raise BadRequestException("User must be a member of the group to accept a task.")

        try:
            accepted = await self.repo.accept_quest(quest.id, current_user.id)
            if not accepted:
                raise BadRequestException("Failed to accept quest. It may have already been accepted by someone else or its status may have changed.")
            logger.info(f"Quest accepted: {quest_public_id} by user {current_user.public_id}")
        except IntegrityError:
            raise

        updated_quest = await self.repo.get_by_public_id(quest_public_id)
        if not updated_quest:
            raise Exception("Failed to retrieve updated quest after accepting.")
        quest_event = QuestUpdateEvent(
            id=updated_quest.id,
            public_id=updated_quest.public_id,
            group_id=updated_quest.group_id,
            group_public_id=group.public_id,
            status=updated_quest.status,
            updated_at=updated_quest.updated_at,
            accepted_by_public_id=current_user.public_id,
            source_user_public_id=current_user.public_id,
        )
        if background_tasks:
            background_tasks.add_task(self.notification_service.notify_group_members_of_taken_quest, quest_event)
        else:
            await self.notification_service.notify_group_members_of_taken_quest(quest_event)
        return updated_quest

    async def delete_quest_by_public_id(self, current_user: User | None, quest_public_id: uuid.UUID, background_tasks: BackgroundTasks):
        quest = await self.repo.get_by_public_id(quest_public_id)
        if not quest:
            raise BadRequestException("Quest not found.")
        if not current_user:
            raise UnauthorizedException("Not authenticated.")

        group = await self.group_repo.get_by_id(quest.group_id)
        if not group:
            raise BadRequestException("Group not found for the quest.")
        current_member = await self.group_member_repo.get_member(current_user.id, quest.group_id)
        if not current_member:
            raise BadRequestException("User must be a member of the group to cancel a task.")
        accepted_by = await self.repo.get_quest_dto_by_public_id(quest_public_id)

        if quest.creator_id != current_user.id and current_member.role not in (MemberRole.ADMIN, MemberRole.OWNER):
            raise BadRequestException("You are not authorized to cancel this task. Only the creator, group admins or owners can cancel a task.")
        if quest.status in (QuestStatus.COMPLETED, QuestStatus.CANCELLED, QuestStatus.EXPIRED):
            raise BadRequestException("This task can no longer be cancelled.")

        # await self.repo.delete(quest.id)
        cancelled = await self.repo.cancel_quest(quest.id)
        if not cancelled:
            raise BadRequestException("Failed to cancel quest. Its status may have changed.")

        updated_quest = await self.repo.get_by_public_id(quest_public_id)
        if not updated_quest:
            raise Exception("Failed to retrieve updated quest after cancelling.")

        logger.info(f"Quest cancelled: {quest_public_id} by user {current_user.public_id}")
        quest_event = QuestUpdateEvent(
            id=updated_quest.id,
            public_id=updated_quest.public_id,
            group_id=updated_quest.group_id,
            group_public_id=group.public_id,
            status=updated_quest.status,
            updated_at=updated_quest.updated_at,
            accepted_by_public_id=accepted_by.accepted_by_public_id if accepted_by else None,
            source_user_public_id=current_user.public_id,
        )
        # TODO [PENDING]: notification plumbing still uses deleted naming/payloads; left unchanged per request.
        background_tasks.add_task(self.notification_service.notify_group_members_of_deleted_quest, quest_event)
