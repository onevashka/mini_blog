from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from .models import MUserRegister
from app.database.db import get_session
from .services import ServicesRoles, ServicesUser


router = APIRouter(prefix='/auth', tags=['AUTH'])


@router.post('/register')
async def register_user(user_data: MUserRegister, db: AsyncSession = Depends(get_session)) -> dict:
    result = await ServicesUser._create_user(user_data=user_data.model_dump(), db=db)
    return result


@router.post('/role/create')
async def create_role(name: str, db: AsyncSession = Depends(get_session)) -> dict:
    result = await ServicesRoles._create_role(name=name, db=db)
    return result