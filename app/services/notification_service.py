
import asyncio
from concurrent.futures import ThreadPoolExecutor

from loguru import logger

from app.models.quest import QuestX
from app.repositories.group_member_repository import GroupMemberRepository
from app.repositories.quest_repository import QuestRepository
from app.repositories.user_repository import UserRepository
from app.schemas.quest import QuestUpdateEvent
from firebase_admin import messaging
'''
fix this
ERROR    | app.services.notification_service:notify_group_members_of_new_quest:76 - Failed to send quest_created notification: Unknown error while making remote service calls: max_workers must be greater than 0
'''

class NotificationService:
    def __init__(
        self, 
        gm_repo: GroupMemberRepository,
        user_repo: UserRepository,
        quest_repo: QuestRepository,
        ):
        self.gm_repo = gm_repo
        self.user_repo = user_repo
        self.quest_repo = quest_repo
    
    def _make_android_config(self) -> messaging.AndroidConfig:
        return messaging.AndroidConfig(
            priority='high',  # escapes Doze — critical
            ttl=3600,         # 1 hour, message dropped if undelivered after this
        )
    
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
        valid_tokens = [member.user.fcm_token for member in gm_w_user_details if member.user.fcm_token and member.user.public_id != questEvent.source_user_public_id]
        skipped_users = [
            member.user.username if member.user.username else 'Unknown' for member in gm_w_user_details 
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
        
        #sending
        message = messaging.MulticastMessage(
            tokens=valid_tokens,
            data={
                'type': 'QUEST_CREATED',
                'group_public_id': str(questEvent.group_public_id),
                'quest_public_id': str(questEvent.public_id),
            },
            android=self._make_android_config(),
        )
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                response = await loop.run_in_executor(executor, messaging.send_each_for_multicast, message)
            logger.info("FCM quest_created sent: {} success, {} fail",
                response.success_count, response.failure_count)
        except Exception as e:
            logger.error(f"Failed to send quest_created notification: {str(e)}")
    
    async def notify_group_members_of_taken_quest(self, questEvent: QuestUpdateEvent):
        gm_w_user_details = await self.gm_repo.fetch_group_members_w_details_by_group_id(questEvent.group_id)
        quest = await self.quest_repo.get(questEvent.id)
        if not quest:
            logger.error(f"Quest with id {questEvent.id} not found for notification.")
            return
        creator = await self.user_repo.get_user_by_id(quest.creator_id)
        if not creator:
            logger.error(f"Creator with id {quest.creator_id} not found for notification.")
            return
        #questX = QuestX.from_orm(quest)
        valid_tokens = [member.user.fcm_token for member in gm_w_user_details if member.user.fcm_token and member.user.public_id != questEvent.source_user_public_id]
        skipped_users = [
            member.user.username if member.user.username else 'Unknown' for member in gm_w_user_details 
            if not member.user.fcm_token or member.user.fcm_token.strip() == ''
            ]
        if skipped_users:
            logger.warning(f"Skipping notification for users without valid FCM tokens: {', '.join(skipped_users)}")
        if not valid_tokens:
            logger.warning(f"No valid FCM tokens found for group_id {questEvent.group_id}. No notifications will be sent.")
        else:
            message = messaging.MulticastMessage(
                tokens=valid_tokens,
                data={
                    'type': 'QUEST_TAKEN',
                    'group_public_id': str(questEvent.group_public_id),
                    'quest_public_id': str(questEvent.public_id),
                    'accepted_by_public_id': str(questEvent.accepted_by_public_id) if questEvent.accepted_by_public_id else '',
                },
                android=self._make_android_config(),
            )
            try:
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor(max_workers=1) as executor:
                    response = await loop.run_in_executor(executor, messaging.send_each_for_multicast, message)
                logger.info("FCM quest_taken sent: {} success, {} fail",
                    response.success_count, response.failure_count)
            except Exception as e:
                logger.error(f"Failed to send quest_taken notification: {str(e)}")
        if creator.fcm_token and creator.fcm_token.strip() != '':
            personal_message = messaging.Message(
                token=creator.fcm_token,
                data={
                    'type': 'YOUR_QUEST_TAKEN',
                    'group_public_id': str(questEvent.group_public_id),
                    'quest_public_id': str(questEvent.public_id),
                    'accepted_by_public_id': str(questEvent.accepted_by_public_id) if questEvent.accepted_by_public_id else '',
                },
                android=self._make_android_config(),
            )
            try:
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor(max_workers=1) as executor:
                    await loop.run_in_executor(executor, messaging.send, personal_message)
                logger.info(f"FCM YOUR_QUEST_TAKEN sent to creator {creator.username} for quest {quest.name}")
            except Exception as e:
                logger.error(f"Failed to send YOUR_QUEST_TAKEN to creator {creator.username} for quest {quest.name}: {str(e)}")
    
    #TODO import in client
    async def notify_creator_of_completed_quest(self, questEvent: QuestUpdateEvent):
        quest = await self.quest_repo.get(questEvent.id)
        if not quest:
            logger.error(f"Quest with id {questEvent.id} not found for notification.")
            return
        creator = await self.user_repo.get_user_by_id(quest.creator_id)
        if not creator:
            logger.error(f"Creator with id {quest.creator_id} not found for notification.")
            return
        if not creator.fcm_token or creator.fcm_token.strip() == '':
            logger.warning(f"Creator {creator.username} does not have a valid FCM token. Cannot send completed quest notification.")
            return
        message = messaging.Message(
            token=creator.fcm_token,
            data={
                'type': 'YOUR_QUEST_COMPLETED',
                'group_public_id': str(questEvent.group_public_id),
                'quest_public_id': str(questEvent.public_id),
                'accepted_by_public_id': str(questEvent.accepted_by_public_id) if questEvent.accepted_by_public_id else '',
            },
            android=self._make_android_config(),
        )
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                await loop.run_in_executor(executor, messaging.send, message)
            logger.info(f"FCM YOUR_QUEST_COMPLETED sent to creator {creator.username} for quest {quest.name}")
        except Exception as e:
            logger.error(f"Failed to send YOUR_QUEST_COMPLETED to creator {creator.username} for quest {quest.name}: {str(e)}")
    
    async def notify_group_members_of_deleted_quest(self, questEvent: QuestUpdateEvent):
        gm_w_user_details = await self.gm_repo.fetch_group_members_w_details_by_group_id(questEvent.group_id)
        valid_tokens = [member.user.fcm_token for member in gm_w_user_details if member.user.fcm_token and member.user.public_id != questEvent.source_user_public_id]
        skipped_users = [
            member.user.username if member.user.username else 'Unknown' for member in gm_w_user_details 
            if not member.user.fcm_token or member.user.fcm_token.strip() == ''
            ]
        if skipped_users:
            logger.warning(f"Skipping notification for users without valid FCM tokens: {', '.join(skipped_users)}")
        if not valid_tokens:
            logger.warning(f"No valid FCM tokens found for group_id {questEvent.group_id}. No notifications will be sent.")
            return
        message = messaging.MulticastMessage(
            tokens=valid_tokens,
            data={
                'type': 'QUEST_DELETED',
                'group_public_id': str(questEvent.group_public_id),
                'quest_public_id': str(questEvent.public_id),
            },
            android=self._make_android_config(),
        )
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                response = await loop.run_in_executor(executor, messaging.send_each_for_multicast, message)
            logger.info("FCM quest_deleted sent: {} success, {} fail",
                response.success_count, response.failure_count)
        except Exception as e:
            logger.error(f"Failed to send quest_deleted notification: {str(e)}")
