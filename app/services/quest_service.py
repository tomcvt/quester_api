
import uuid

from loguru import logger
from fastapi import BackgroundTasks
from sqlalchemy.exc import IntegrityError
from app.exceptions import BadRequestException, UnauthorizedException
from app.models.user import User
from app.models.quest import Quest, NewQuest, UpdateQuest
from app.repositories.group_member_repository import GroupMemberRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.quest_repository import QuestRepository
from app.schemas.quest import CreateQuestRequest, QuestUpdateEvent
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


    async def create_quest(self, current_user: User, quest_request: CreateQuestRequest, background_tasks: BackgroundTasks) -> Quest:
        group_id = await self.group_repo.get_group_id_by_public_id(quest_request.group_public_id)
        if not group_id:
            #raise ValueError(f"Group with public_id {quest_request.group_public_id} not found.")
            # Alternatively, you could raise a custom exception here instead of ValueError. For example just BadRequest to bubble up to the controller and return a 400 response.
            raise BadRequestException(f"Group with public_id {quest_request.group_public_id} not found.")
        if not current_user:
            raise BadRequestException("Not authenticated.")
        #TODO - check if user is a member of the group before allowing quest creation
        is_member = await self.group_member_repo.is_member(current_user.id, group_id)
        if not is_member:
            raise BadRequestException("User must be a member of the group to create a task.")
        #TODO validatiion
        quest_data = NewQuest(
            group_id=group_id,
            name=quest_request.name,
            data=quest_request.data,
            deadline=quest_request.deadline,
            address=quest_request.address,
            contact_number=quest_request.contact_number,
            contact_info=quest_request.contact_info,
            type=quest_request.type,
            inclusive=quest_request.inclusive,
            status=quest_request.status,
            creator_id=current_user.id
        )
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
            group_id=newQuest.group_id,
            status=newQuest.status,
            updated_at=newQuest.updated_at
        )
        background_tasks.add_task(
            self.notification_service.notify_group_members_of_new_quest, questEvent
        )
        return newQuest
    
    async def accept_quest(self, current_user: User, quest_public_id: uuid.UUID):
        #TODO - implement accept quest logic here, this will likely involve creating a new entry in a QuestAcceptance table that tracks which users have accepted which quests, and possibly sending notifications to the quest creator and other group members.
        pass
        
    
    async def delete_quest_by_public_id(self, current_user: User | None, quest_public_id: uuid.UUID):
        quest = await self.repo.get_by_public_id(quest_public_id)
        if not quest:
            raise BadRequestException(f"Quest not found.")
        if not current_user:
            raise UnauthorizedException("Not authenticated.")
        if quest.creator_id != current_user.id:
            raise BadRequestException("User must be the creator of the task to delete it.")
        await self.repo.delete(quest.id)
    