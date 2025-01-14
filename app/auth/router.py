from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException
from app.database.db import get_session
from .models import MUserRegister, MUserAuth
from .dao import UserDAO
from .auth import get_password_hash, auth_user, get_access_token, get_current_user, get_current_user_optional
from fastapi import Response
from .schemas import User


router = APIRouter(prefix='/auth', tags=['AUTH'])


@router.post('/register')
async def register_user(user_data: MUserRegister, db: AsyncSession = Depends(get_session)) -> dict:
    user = await UserDAO.find_one_or_none(filters=user_data, db=db)
    if user:
        raise HTTPException(status_code=409, detail='Пользователь с такими данными уже существует')
    user_dict = user_data.model_dump()
    user_dict['password_hash'] = get_password_hash(user_data.password_hash)
    await UserDAO.add(user_dict, db=db)
    return {'message': f'Вы успешно зарегистрированы!'}


@router.post('/login')
async def login(response: Response, user_data: MUserAuth, db: AsyncSession = Depends(get_session)) -> dict:
    check = await auth_user(email=user_data.email, password=user_data.password_hash, db=db)
    if check is None:
        raise HTTPException(status_code=401, detail='Неверная почта или пароль')
    access_token = get_access_token({'sub': str(check.id)})
    response.set_cookie(key='user_access_token', value=access_token, httponly=True)
    return {'access_token': access_token, 'refresh_token': None}


@router.get('/me')
async def get_me(user_data: User = Depends(get_current_user_optional)):
    return user_data


@router.post("/logout/")
async def logout_user(response: Response):
    response.delete_cookie(key="user_access_token")
    return {'message': 'Пользователь успешно вышел из системы'}