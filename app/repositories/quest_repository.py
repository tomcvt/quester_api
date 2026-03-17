from datetime import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import quest
from app.models.quest import NewQuest, Quest, UpdateQuest
from app.models.user import User
from app.schemas.quest import QuestWithUser


class QuestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, quest_data: NewQuest) -> Quest:
        quest = Quest.new(quest_data)
        self.db.add(quest)
        await self.db.commit()
        return quest

    async def get(self, quest_id: int) -> Quest | None:
        result = await self.db.execute(select(Quest).filter_by(id=quest_id))
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
    
    async def fetch_quests_by_group_id_after_timestamp(self, group_id: int, timestamp: datetime) -> list[QuestWithUser]:
        result = await self.db.execute(
            select(Quest, User.public_id)
            .join(User, User.id == Quest.creator_id)
            .where(
                Quest.group_id == group_id,
                Quest.updated_at > timestamp
            )
        )
        return [
            QuestWithUser(
                id=quest.id,
                public_id=quest.public_id,
                name=quest.name,
                data=quest.data,
                type=quest.type,
                inclusive=quest.inclusive,
                status=quest.status,
                creator_public_id=user_public_id,
                created_at=quest.created_at,
                updated_at=quest.updated_at
            )
            for quest, user_public_id in result.all()
        ]
    