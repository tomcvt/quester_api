
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo
    
    async def get_user_by_public_id(self, public_id: str):
        return await self.repo.get_user_by_public_id(public_id)
    
    async def get_user_by_id(self, id: int):
        return await self.repo.get_user_by_id(id)
    
    