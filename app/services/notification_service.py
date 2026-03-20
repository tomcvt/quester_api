
from loguru import logger

from app.models.quest import QuestX
from app.repositories.group_member_repository import GroupMemberRepository
from app.repositories.quest_repository import QuestRepository
from app.repositories.user_repository import UserRepository
from app.schemas.quest import QuestUpdateEvent


class NotificationService:
    def __init__(
        self, gm_repo: GroupMemberRepository,
        user_repo: UserRepository,
        quest_repo: QuestRepository,
        ):
        self.gm_repo = gm_repo
        self.user_repo = user_repo
        self.quest_repo = quest_repo
    
    async def notify_group_members_of_new_quest(self, questEvent: QuestUpdateEvent):
        gm_w_user_details = await self.gm_repo.fetch_group_members_w_details_by_group_id(questEvent.group_id)
        quest = await self.quest_repo.get(questEvent.id)
        if not quest:
            logger.error(f"Quest with id {questEvent.id} not found for notification.")
            return
        creator = await self.user_repo.get_user_by_id(quest.creator_id)
        if not creator:
            logger.error(f"Creator with id {quest.creator_id} not found for notification.")
            return
        questX = QuestX.from_orm(quest)
        valid_tokens = [member.user.fcm_token for member in gm_w_user_details if member.user.fcm_token]
        skipped_users = [
            member.user.username for member in gm_w_user_details 
            if not member.user.fcm_token or member.user.fcm_token.strip() == ''
            ]
        if skipped_users:
            logger.warning(f"Skipping notification for users without valid FCM tokens: {', '.join(skipped_users)}")
        if not valid_tokens:
            logger.warning(f"No valid FCM tokens found for group_id {questEvent.group_id}. No notifications will be sent.")
            return
        if not quest.inclusive:
            if creator.fcm_token in valid_tokens:
                valid_tokens.remove(creator.fcm_token)
        else:
            logger.info(f"Quest {quest.name} is inclusive, sending notifications to all members including the creator.")
        #TODO - implement actual notification sending logic here using FCM or another push notification service.
        
