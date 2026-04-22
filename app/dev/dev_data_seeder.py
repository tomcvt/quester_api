

import asyncio
from datetime import datetime, timedelta
import uuid

from fastapi import BackgroundTasks, FastAPI
from fastapi.concurrency import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.group import Group
from app.models.quest import NewQuest, QuestStatus, QuestType
from app.models.user import User
from app.repositories.group_member_repository import GroupMemberRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.quest_repository import QuestRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegistrationRequest
from app.schemas.group import CreateGroupRequest
from app.services.auth_service import AuthService
from app.services.group_service import GroupService
from app.services.notification_service import NotificationService
from app.services.quest_service import QuestService
from app.services.user_service import UserService


class DevDataSeeder:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.group_repo = GroupRepository(db)
        self.quest_repo = QuestRepository(db)
        self.gm_repo = GroupMemberRepository(db)
        self.auth_service = AuthService(self.user_repo)
        
        self.notification_service = NotificationService(
            self.gm_repo,
            self.user_repo,
            self.quest_repo
        )
        self.user_service = UserService(self.user_repo, self.notification_service)
        self.group_service = GroupService(
            self.group_repo, 
            self.gm_repo, 
            self.quest_repo,
            self.user_repo,
            self.notification_service
        )
        self.quest_service = QuestService(
            self.quest_repo, 
            self.group_repo, 
            self.gm_repo, 
            self.notification_service # no need for notification service in seeding
        )
    
    uuidNIL13 = uuid.UUID('00000000-0000-0000-0000-000000000013')
    uuidNIL14 = uuid.UUID('00000000-0000-0000-0000-000000000014')

    async def seed(self):
        # Implement your data seeding logic here
        # i will implement later using services
        superuser_request = RegistrationRequest(
            device_id="superuser_device",
            installation_id=str(uuid.UUID(int=7)),
            username="superuser",
            password="125", #TODO
            phone_number="0000000000"
        )
        registration_request_1 = RegistrationRequest(
            device_id="test_device_1",
            installation_id=str(self.uuidNIL13),
            username="testuser1",
            password="",
            phone_number="1234567890"
        )
        registration_request_2 = RegistrationRequest(
            device_id="test_device_2",
            installation_id=str(self.uuidNIL14),
            username="testuser2",
            password="",
            phone_number="0987654321"
        )
        superuser = await self.auth_service.register_user(superuser_request)
        logger.info(f"Registered superuser: {superuser.username}")
        user1 = await self.auth_service.register_user(registration_request_1)
        user2 = await self.auth_service.register_user(registration_request_2)
        logger.info(f"Registered users: {user1.username} and {user2.username}")
        group_request = CreateGroupRequest(
            name="PartyTest",
            password="1234"
        )
        group = await self.group_service.create_group(
            current_user=user1,
            request=group_request
        )
        await self.group_service.join_group(
            current_user=user2,
            group_public_id=group.public_id,
        )
        logger.info(f"Created group: {group.name} with public_id: {group.public_id}")
        logger.info(f"User {user1.username} and {user2.username} joined the group {group.name}")
    
    async def create_quest_for_testing(self, creator_user: User, group: Group):
        new_quest = NewQuest(
            group_id=group.id,
            name="Test Quest",
            description="This is a test quest.",
            date=datetime.utcnow(),
            deadline_start=datetime.utcnow() + timedelta(minutes=2),
            deadline_end=datetime.utcnow() + timedelta(minutes=10),
            address=None,
            contact_number=None,
            contact_info=None,
            data=None,
            type=QuestType.JOB,
            inclusive=False,
            status=QuestStatus.STARTED,
            creator_id=creator_user.id
        )
        quest = await self.quest_service.create_quest(creator_user, new_quest)
        logger.info(f"Created quest: {quest.name} with public_id: {quest.public_id} in group {group.name}")
    
    async def create_quest_test_1(self):
        users1 = await self.user_repo.get_users_by_username("testuser1")
        user1 = users1[0] if users1 else None
        if not user1:
            logger.error("User testuser1 not found for quest creation.")
            return
        group = await self.group_repo.get_by_name("PartyTest")
        if not group:
            logger.error("Group PartyTest not found for quest creation.")
            return
        await self.create_quest_for_testing(user1, group)
        
        


@asynccontextmanager
async def dev_data_seeder_lifespan(app: FastAPI):
    from app.core.database import AsyncSessionLocal
    from app.core.config import settings

    if settings.persistence_mode in ('memory', 'sqlite'):
        async with AsyncSessionLocal() as session:
            seeder = DevDataSeeder(db=session)
            await seeder.seed()
        logger.info("Dev data seeded successfully.")
    yield