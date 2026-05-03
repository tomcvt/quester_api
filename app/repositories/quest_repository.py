from datetime import datetime
import uuid

from loguru import logger
from sqlalchemy import and_, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.group import Group
from app.models.quest import NewQuest, Quest, QuestStatus, UpdateQuest
from app.models.user import User
from app.schemas.quest import QuestSyncDTO, QuestWithUserPId


class QuestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def accept_quest(self, quest_id: int, user_id: int) -> bool:
        try:
            statement = (
                update(Quest)
                .where(
                    Quest.id == quest_id,
                    Quest.accepted_by_id.is_(None),
                    Quest.status == QuestStatus.OPEN,
                )
                .values(accepted_by_id=user_id, status=QuestStatus.ACCEPTED, updated_at=datetime.now())
                .execution_options(synchronize_session="fetch")
            )
            result = await self.db.execute(statement)
            await self.db.commit()
            rowcount = getattr(result, "rowcount", 0) or 0
            logger.info(f"Accept quest update rowcount: {rowcount}")
            return rowcount > 0
        except IntegrityError:
            await self.db.rollback()
            raise

    async def complete_quest(self, quest_id: int, user_id: int) -> bool:
        try:
            statement = (
                update(Quest)
                .where(
                    Quest.id == quest_id,
                    Quest.accepted_by_id == user_id,
                    Quest.status == QuestStatus.ACCEPTED,
                )
                .values(status=QuestStatus.COMPLETED, updated_at=datetime.now())
                .execution_options(synchronize_session="fetch")
            )
            result = await self.db.execute(statement)
            await self.db.commit()
            rowcount = getattr(result, "rowcount", 0) or 0
            logger.info(f"Complete quest update rowcount: {rowcount}")
            return rowcount > 0
        except IntegrityError:
            await self.db.rollback()
            raise
    
    async def open_quest(self, quest_id: int) -> bool:
        try:
            statement = (
                update(Quest)
                .where(
                    Quest.id == quest_id,
                    Quest.status == QuestStatus.CREATED,
                )
                .values(status=QuestStatus.OPEN, updated_at=datetime.now())
                .execution_options(synchronize_session="fetch")
            )
            result = await self.db.execute(statement)
            await self.db.commit()
            rowcount = getattr(result, "rowcount", 0) or 0
            logger.info(f"Open quest update rowcount: {rowcount}")
            return rowcount > 0
        except IntegrityError:
            await self.db.rollback()
            raise

    async def cancel_quest(self, quest_id: int) -> bool:
        try:
            statement = (
                update(Quest)
                .where(
                    Quest.id == quest_id,
                    Quest.status.in_([
                        QuestStatus.CREATED,
                        QuestStatus.OPEN,
                        QuestStatus.ACCEPTED,
                    ]),
                )
                .values(status=QuestStatus.CANCELLED, updated_at=datetime.now())
                .execution_options(synchronize_session="fetch")
            )
            result = await self.db.execute(statement)
            await self.db.commit()
            rowcount = getattr(result, "rowcount", 0) or 0
            logger.info(f"Cancel quest update rowcount: {rowcount}")
            return rowcount > 0
        except IntegrityError:
            await self.db.rollback()
            raise

    async def reward_quest(self, quest_id: int) -> bool:
        try:
            statement = (
                update(Quest)
                .where(
                    Quest.id == quest_id,
                    Quest.status == QuestStatus.COMPLETED,
                )
                .values(status=QuestStatus.REWARDED, updated_at=datetime.now())
                .execution_options(synchronize_session="fetch")
            )
            result = await self.db.execute(statement)
            await self.db.commit()
            rowcount = getattr(result, "rowcount", 0) or 0
            logger.info(f"Reward quest update rowcount: {rowcount}")
            return rowcount > 0
        except IntegrityError:
            await self.db.rollback()
            raise

    async def create(self, quest_data: NewQuest) -> Quest:
        quest = Quest.new(quest_data)
        self.db.add(quest)
        await self.db.commit()
        await self.db.refresh(quest)
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
        for key, value in quest_data.model_dump(exclude_unset=True).items():
            setattr(quest, key, value)
        await self.db.commit()
        await self.db.refresh(quest)
        return quest

    async def fetch_quests_by_group_id_after_timestamp(self, group_id: int, timestamp: datetime) -> list[QuestWithUserPId]:
        creator = aliased(User)
        accepter = aliased(User)
        result = await self.db.execute(
            select(Quest, creator.public_id, accepter.public_id)
            .join(creator, creator.id == Quest.creator_id)
            .outerjoin(accepter, accepter.id == Quest.accepted_by_id)
            .where(Quest.group_id == group_id, Quest.updated_at > timestamp)
        )
        return [
            QuestWithUserPId(
                id=quest.id,
                public_id=quest.public_id,
                name=quest.name,
                description=quest.description,
                start_time=quest.start_time,
                deadline=quest.deadline,
                address=quest.address,
                data=quest.data,
                reward_type=quest.reward_type,
                reward_value=quest.reward_value,
                inclusive=quest.inclusive,
                status=quest.status,
                creator_public_id=creator_public_id,
                accepted_by_public_id=accepter_public_id,
                created_at=quest.created_at,
                updated_at=quest.updated_at,
                automatic_reward=quest.automatic_reward,
            )
            for quest, creator_public_id, accepter_public_id in result.all()
        ]

    async def get_quests_page(
        self,
        page: int,
        size: int,
        status: QuestStatus | None = None,
        group_id: int | None = None,
        creator_id: int | None = None,
        name: str | None = None,
    ) -> tuple[list[Quest], int]:
        filters = []
        if status is not None:
            filters.append(Quest.status == status)
        if group_id is not None:
            filters.append(Quest.group_id == group_id)
        if creator_id is not None:
            filters.append(Quest.creator_id == creator_id)
        if name is not None:
            filters.append(Quest.name.ilike(f"%{name}%"))

        statement = select(Quest).order_by(Quest.id).limit(size).offset(page * size)
        count_statement = select(func.count()).select_from(Quest)
        if filters:
            statement = statement.where(and_(*filters))
            count_statement = count_statement.where(and_(*filters))

        quests_result = await self.db.execute(statement)
        count_result = await self.db.execute(count_statement)
        return list(quests_result.scalars().all()), count_result.scalar_one()

    async def get_quest_dto_by_public_id(self, public_id: uuid.UUID) -> QuestSyncDTO | None:
        creator = aliased(User)
        accepter = aliased(User)
        group = aliased(Group)
        result = await self.db.execute(
            select(Quest, group.public_id, creator.public_id, accepter.public_id)
            .join(group, group.id == Quest.group_id)
            .join(creator, creator.id == Quest.creator_id)
            .outerjoin(accepter, accepter.id == Quest.accepted_by_id)
            .where(Quest.public_id == public_id)
        )
        row = result.first()
        if not row:
            return None
        quest, group_public_id, creator_public_id, accepter_public_id = row
        return QuestSyncDTO(
            group_public_id=group_public_id,
            public_id=quest.public_id,
            name=quest.name,
            description=quest.description,
            start_time=quest.start_time,
            deadline=quest.deadline,
            address=quest.address,
            data=quest.data,
            reward_type=quest.reward_type,
            reward_value=quest.reward_value,
            inclusive=quest.inclusive,
            automatic_reward=quest.automatic_reward,
            status=quest.status,
            creator_public_id=creator_public_id,
            created_at=quest.created_at,
            updated_at=quest.updated_at,
            accepted_by_public_id=accepter_public_id,
        )

    