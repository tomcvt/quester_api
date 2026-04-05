from datetime import datetime
import uuid
from loguru import logger

from sqlalchemy import select, update
from sqlalchemy.orm import aliased
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import quest
from app.models.quest import NewQuest, Quest, UpdateQuest, QuestStatus
from app.models.user import User
from app.schemas.quest import QuestWithUserPId


class QuestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def accept_quest(self, quest_id: int, user_id: int) -> bool:
        """
        Attempt to accept a quest by setting accepted_by_id and status to ACCEPTED if not already accepted and status is STARTED.
        Returns True if the quest was accepted, False otherwise.
        """
        try:
            stm = (
                update(Quest)
                .where(
                    Quest.id == quest_id,
                    Quest.accepted_by_id == None,
                    Quest.status == QuestStatus.STARTED
                )
                .values(accepted_by_id=user_id, status=QuestStatus.ACCEPTED, updated_at=datetime.now())
                .execution_options(synchronize_session=False)
            )
            result = await self.db.execute(stm)
            await self.db.commit()
            # SQLAlchemy 2.x async result may not have rowcount directly, use _real_result.rowcount if needed
            rowcount = getattr(result, 'rowcount', None)
            logger.info(f"Accept quest update result: {result}, rowcount: {rowcount}")
            if rowcount is None and hasattr(result, '_real_result'):
                rowcount = getattr(result._real_result, 'rowcount', None)
                logger.info(f"Accept quest real result rowcount: {rowcount}")
            if rowcount is None:
                rowcount = 0
                logger.warning("Could not determine rowcount from result, defaulting to 0.")
            return rowcount > 0
        except IntegrityError:
            await self.db.rollback()
            raise
    
    async def complete_quest(self, quest_id: int, user_id: int) -> bool:
        """
        Attempt to complete a quest by setting status to COMPLETED if accepted_by_id matches user_id and status is ACCEPTED.
        Returns True if the quest was completed, False otherwise.
        """
        try:
            stm = (
                update(Quest)
                .where(
                    Quest.id == quest_id,
                    Quest.accepted_by_id == user_id,
                    Quest.status == QuestStatus.ACCEPTED
                )
                .values(status=QuestStatus.COMPLETED, updated_at=datetime.now())
                .execution_options(synchronize_session=False)
            )
            result = await self.db.execute(stm)
            await self.db.commit()
            rowcount = getattr(result, 'rowcount', None)
            logger.info(f"Complete quest update result: {result}, rowcount: {rowcount}")
            if rowcount is None and hasattr(result, '_real_result'):
                rowcount = getattr(result._real_result, 'rowcount', None)
                logger.info(f"Complete quest real result rowcount: {rowcount}")
            if rowcount is None:
                rowcount = 0
                logger.warning("Could not determine rowcount from result, defaulting to 0.")
            return rowcount > 0
        except IntegrityError:
            await self.db.rollback()
            raise
    
    async def create(self, quest_data: NewQuest) -> Quest:
        quest = Quest.new(quest_data)
        self.db.add(quest)
        await self.db.commit()
        logger.info(f"Quest created: {quest}")
        return quest

    async def get(self, quest_id: int) -> Quest | None:
        result = await self.db.execute(select(Quest).filter_by(id=quest_id))
        return result.scalars().first()
    
    async def get_by_public_id(self, public_id: uuid.UUID) -> Quest | None:
        result = await self.db.execute(select(Quest).filter_by(public_id=public_id))
        return result.scalars().first()

    async def update(self, quest_id: int, quest_data: UpdateQuest) -> Quest | None:
        quest = await self.get(quest_id)
        if not quest:
            return None
        for key, value in quest_data.dict(exclude_unset=True).items():
            setattr(quest, key, value)
        await self.db.commit()
        return quest

    async def delete(self, quest_id: int) -> bool:
        quest = await self.get(quest_id)
        if not quest:
            return False
        await self.db.delete(quest)
        await self.db.commit()
        return True
    
    async def fetch_quests_by_group_id_after_timestamp(self, group_id: int, timestamp: datetime) -> list[QuestWithUserPId]:
        creator = aliased(User)
        accepter = aliased(User)
        result = await self.db.execute(
            select(Quest, creator.public_id, accepter.public_id)
            .join(creator, creator.id == Quest.creator_id)
            .outerjoin(accepter, accepter.id == Quest.accepted_by_id)
            .where(
                Quest.group_id == group_id,
                Quest.updated_at > timestamp
            )
        )
        return [
            QuestWithUserPId(
                id=quest.id,
                public_id=quest.public_id,
                name=quest.name,
                data=quest.data,
                deadline=quest.deadline,
                address=quest.address,
                contact_number=quest.contact_number,
                contact_info=quest.contact_info,
                type=quest.type,
                inclusive=quest.inclusive,
                status=quest.status,
                creator_public_id=creator_public_id,
                accepted_by_public_id=accepter_public_id,
                created_at=quest.created_at,
                updated_at=quest.updated_at
            )
            for quest, creator_public_id, accepter_public_id in result.all()
        ]
    