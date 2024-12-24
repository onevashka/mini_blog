from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import Role, User
from .models import MUserRegister
from .auth import get_password_hash


class ServicesRoles():

    @classmethod
    async def _create_role(cls, name: str, db: AsyncSession) -> dict:
        new_role = Role(name=name)
        db.add(new_role)
        await db.commit()
        await db.refresh(new_role)
        return {'message': 'Role created successfully'}
    

class ServicesUser():

    @classmethod
    async def _create_user(cls, user_data: dict, db: AsyncSession) -> dict:
        password_hash = get_password_hash(user_data['password'])
        del user_data['password']
        user_data['password_hash'] = password_hash
        new_user = User(**user_data)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return {'message': 'User created successfully'}