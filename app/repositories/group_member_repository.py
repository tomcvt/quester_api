from datetime import datetime
from typing import Sequence, Tuple
import uuid

from sqlalchemy import Row, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.models import group
from app.models.group_member import GroupMember, GroupMemberX, MemberRole
from app.exceptions import GroupNameTakenException, UserAlreadyInGroupException
from app.models.user import User, UserX
from app.schemas.group_member import GroupMemberWithUser, GroupMemberWithUserSlim

class GroupMemberRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_user_to_group(self, user: User, group: group.Group) -> GroupMember:
        member = GroupMember(user_id=user.id, group_id=group.id, role=MemberRole.MEMBER)
        try:
            self.db.add(member)
            await self.db.commit()
            await self.db.refresh(member)
            return member
        except IntegrityError:
            await self.db.rollback()
            raise UserAlreadyInGroupException(f"User {member.user_id} is already a member of group {member.group_id}.")
    
    async def add_user_to_group_with_role(self, user: User, group: group.Group, role: MemberRole) -> GroupMember:
        member = GroupMember(user_id=user.id, group_id=group.id, role=role)
        try:
            self.db.add(member)
            await self.db.commit()
            await self.db.refresh(member)
            return member
        except IntegrityError:
            await self.db.rollback()
            raise UserAlreadyInGroupException(f"User {member.user_id} is already a member of group {member.group_id}.")
        
    async def fetch_group_members_w_details_after_timestamp(self, group_id: int, timestamp: datetime) -> list[GroupMemberWithUserSlim]:
        result = await self.db.execute(
            select(GroupMember, User.username, User.public_id)
            .join(User, User.id == GroupMember.user_id)
            .where(
                GroupMember.group_id == group_id,
                GroupMember.updated_at > timestamp
            )
        )
        '''
        result2 = result.all()
        varss = result2[0][0]
        vars2: Row[Tuple[GroupMember, str, uuid.UUID]] = result2[0]
        vars3: Sequence[Row[tuple[GroupMember, str, uuid.UUID]]] = result2
        x = []
        for row in vars3:
            member = row[0]
            username = row[1]
            user_public_id = row[2]
            x.append(GroupMemberWithUser(
                id=member.id,
                group_id=member.group_id,
                user_id=member.user_id,
                role=member.role,
                updated_at=member.updated_at,
                username=username,
                user_public_id=user_public_id
            ))
        '''
        '''
        return [
            GroupMemberWithUser(
            id=row[0].id,
            group_id=row[0].group_id,
            user_id=row[0].user_id,
            role=row[0].role,
            updated_at=row[0].updated_at,
            username=row[1],
            user_public_id=row[2]
        ) for row in result.all()]
        '''
        return [
            GroupMemberWithUserSlim(
                id=member.id,
                group_id=member.group_id,
                user_id=member.user_id,
                role=member.role,
                updated_at=member.updated_at,
                username=username,
                user_public_id=user_public_id
            )
            for member, username, user_public_id in result.all()
        ]
    
    async def fetch_group_members_w_details_by_group_id(self, group_id: int) -> list[GroupMemberWithUser]:
        result = await self.db.execute(
            select(GroupMember, User)
            .join(User, User.id == GroupMember.user_id)
            .where(GroupMember.group_id == group_id)
        )
        return [
            GroupMemberWithUser(
                group_member=GroupMemberX.from_orm(member),
                user=UserX.from_orm(user)
            )
            for member, user in result.all()
        ]
            
    
    async def get_group_members(self, group_id: int) -> list[GroupMember]:
        result = await self.db.execute(
            select(GroupMember).where(GroupMember.group_id == group_id)
        )
        return list(result.scalars().all())
    
    async def is_member(self, user_id: int, group_id: int) -> bool:
        result = await self.db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id
            )
        )
        member = result.scalars().first()
        return member is not None
