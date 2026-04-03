

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

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
        self.user_service = UserService(self.user_repo)
        self.notification_service = NotificationService(
            self.gm_repo,
            self.user_repo,
            self.quest_repo
        )
        self.group_service = GroupService(
            self.group_repo, 
            self.gm_repo, 
            self.quest_repo
        )
        self.quest_service = QuestService(
            self.quest_repo, 
            self.group_repo, 
            self.gm_repo, 
            self.notification_service # no need for notification service in seeding
        )

    async def seed(self):
        # Implement your data seeding logic here
        # i will implement later using services
        registration_request_1 = RegistrationRequest(
            installation_id="test_installation_1",
            username="testuser1",
            password="",
        )
        registration_request_2 = RegistrationRequest(
            installation_id="test_installation_2",
            username="testuser2",
            password="",
        )
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