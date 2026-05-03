from datetime import datetime
import uuid

from fastapi import BackgroundTasks
from loguru import logger
from sqlalchemy.exc import IntegrityError

from app.exceptions import BadRequestException, UnauthorizedException
from app.models.group_member import MemberRole
from app.models.quest import NewQuest, Quest, QuestStatus, RewardType
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

        if quest_request.status == QuestStatus.OPEN:
            effective_start_time = datetime.utcnow()
        elif quest_request.status == QuestStatus.CREATED:
            if quest_request.start_time is None:
                raise BadRequestException("Quest with status CREATED must provide start_time.")
            if quest_request.start_time <= datetime.utcnow():
                raise BadRequestException("Quest start_time must be in the future.")
            effective_start_time = quest_request.start_time
        else:
            raise BadRequestException("Quests can only be created with status OPEN or CREATED.")

        new_quest = NewQuest(
            group_id=group_id,
            name=quest_request.name,
            description=quest_request.description,
            start_time=effective_start_time,
            deadline=quest_request.deadline,
            address=quest_request.address,
            data=quest_request.data,
            reward_type=quest_request.reward_type,
            reward_value=quest_request.reward_value,
            inclusive=quest_request.inclusive,
            automatic_reward=quest_request.automatic_reward,
            status=quest_request.status,
            creator_id=current_user.id,
        )
        return await self.create_quest(current_user, new_quest, background_tasks, group_public_id=quest_request.group_public_id)

    async def complete_quest(self, current_user: User, quest_public_id: uuid.UUID, background_tasks: BackgroundTasks) -> Quest:
        quest = await self.repo.get_by_public_id(quest_public_id)
        if not quest:
            raise BadRequestException("Quest not found.")
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

        if updated_quest.automatic_reward:
            await self._apply_reward(updated_quest, group, background_tasks)
            updated_quest = await self.repo.get_by_public_id(quest_public_id) or updated_quest

        return updated_quest

    async def _apply_reward(self, quest: Quest, group, background_tasks: BackgroundTasks) -> None:
        """Transition COMPLETED → REWARDED and credit the accepter's currency if applicable."""
        rewarded = await self.repo.reward_quest(quest.id)
        if not rewarded:
            logger.warning(f"Auto-reward failed for quest {quest.public_id}; may have already been rewarded.")
            return
        if quest.reward_type == RewardType.CURRENCY and quest.reward_value and quest.accepted_by_id:
            try:
                amount = int(quest.reward_value)
            except (ValueError, TypeError):
                logger.warning(f"Quest {quest.public_id} has non-integer reward_value '{quest.reward_value}'; skipping currency increment.")
                amount = 0
            if amount > 0:
                await self.group_member_repo.increment_currency(quest.accepted_by_id, quest.group_id, amount)
                logger.info(f"Credited {amount} currency to user_id={quest.accepted_by_id} in group_id={quest.group_id}")
        accepter_public_id = None
        if quest.accepted_by_id:
            from app.models.user import User as UserModel
            from sqlalchemy import select
            result = await self.repo.db.execute(
                select(UserModel.public_id).where(UserModel.id == quest.accepted_by_id)
            )
            row = result.first()
            accepter_public_id = row[0] if row else None
        reward_event = QuestUpdateEvent(
            id=quest.id,
            public_id=quest.public_id,
            group_id=quest.group_id,
            group_public_id=group.public_id,
            status=QuestStatus.REWARDED,
            updated_at=quest.updated_at,
            accepted_by_public_id=accepter_public_id,
        )
        background_tasks.add_task(self.notification_service.notify_group_members_of_rewarded_quest, reward_event)

    async def reward_quest(self, current_user, quest_public_id: uuid.UUID, background_tasks: BackgroundTasks) -> Quest:
        quest = await self.repo.get_by_public_id(quest_public_id)
        if not quest:
            raise BadRequestException("Quest not found.")
        if quest.creator_id != current_user.id:
            raise BadRequestException("Only the quest creator can issue a reward.")
        if quest.status != QuestStatus.COMPLETED:
            raise BadRequestException("Quest must be in COMPLETED status to be rewarded.")

        group = await self.group_repo.get_by_id(quest.group_id)
        if not group:
            raise BadRequestException("Group not found for the quest.")

        await self._apply_reward(quest, group, background_tasks)
        updated_quest = await self.repo.get_by_public_id(quest_public_id)
        if not updated_quest:
            raise Exception("Failed to retrieve updated quest after rewarding.")
        return updated_quest

    async def accept_quest(self, current_user: User, quest_public_id: uuid.UUID, background_tasks: BackgroundTasks) -> Quest:
        quest = await self.repo.get_by_public_id(quest_public_id)
        if not quest:
            raise BadRequestException("Quest not found.")
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
    
    async def open_quest(self, current_user: User, quest_public_id: uuid.UUID, background_tasks: BackgroundTasks) -> Quest:
        quest = await self.repo.get_by_public_id(quest_public_id)
        if not quest:
            raise BadRequestException("Quest not found.")
        if quest.status != QuestStatus.CREATED:
            raise BadRequestException("Only quests in CREATED status can be opened.")
        if quest.creator_id != current_user.id:
            raise BadRequestException("Only the creator can open the quest.")

        group = await self.group_repo.get_by_id(quest.group_id)
        if not group:
            raise BadRequestException("Group not found for the quest.")
        is_member = await self.group_member_repo.is_member(current_user.id, quest.group_id)
        if not is_member:
            raise BadRequestException("User must be a member of the group to open a task.")
        if current_user.id != quest.creator_id:
            raise BadRequestException("Only the creator can open the quest.")

        try:
            opened = await self.repo.open_quest(quest.id)
            if not opened:
                raise BadRequestException("Failed to open quest. Its status may have already been changed.")
            logger.info(f"Quest opened: {quest_public_id} by user {current_user.public_id}")
        except IntegrityError:
            raise

        updated_quest = await self.repo.get_by_public_id(quest_public_id)
        if not updated_quest:
            raise Exception("Failed to retrieve updated quest after opening.")
        quest_event = QuestUpdateEvent(
            id=updated_quest.id,
            public_id=updated_quest.public_id,
            group_id=updated_quest.group_id,
            group_public_id=group.public_id,
            status=updated_quest.status,
            updated_at=updated_quest.updated_at,
        )
        # TODO [PENDING]: delayed-start quests currently emit a new-quest notification at creation time, not at open time. When the start-time queue is added, notification timing may need to move to this point.
        if background_tasks:
            background_tasks.add_task(self.notification_service.notify_group_members_of_new_quest, quest_event)
        else:
            await self.notification_service.notify_group_members_of_new_quest(quest_event)
        return updated_quest

    async def delete_quest_by_public_id(self, current_user: User, quest_public_id: uuid.UUID, background_tasks: BackgroundTasks):
        quest = await self.repo.get_by_public_id(quest_public_id)
        if not quest:
            raise BadRequestException("Quest not found.")

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
