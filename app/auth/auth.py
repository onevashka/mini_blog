from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.config import ALGORITHM, get_auth_data, SECRET_KEY
from pydantic import EmailStr
from .dao import UserDAO
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Response, Request, HTTPException, Depends
from app.database.db import get_session
from .schemas import User


pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_verify_password(plain_password: str, hashed_password: str) -> str:
    return pwd_context.verify(plain_password, hashed_password)


def get_access_token(data: dict) -> bool:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({'exp': expire})
    auth_data = get_auth_data()
    encode_jwt = jwt.encode(to_encode, auth_data['secret_key'], algorithm=auth_data['algorithm'])
    return encode_jwt


async def auth_user(email: EmailStr, password: str, db: AsyncSession):
    user_data = {'email': email}
    user = await UserDAO.find_one_or_none(filters=user_data, db=db)
    if user and get_verify_password(password, user.password_hash):
        return user
    return None


def get_token(request: Request) -> str | None:
    token = request.cookies.get('user_access_token')
    return token


def docode(token: str, auth_data: dict) -> dict:
    try:
        payload = jwt.decode(token, auth_data['secret_key'], algorithms=[auth_data['algorithm']])
    except JWTError:
        raise HTTPException(status_code=401, detail='Токен не валидный!')   
    return payload


async def get_current_user(db: AsyncSession = Depends(get_session), token: str = Depends(get_token)):
    auth_data = get_auth_data()
    payload = docode(token, auth_data)
    
    expire = payload.get('exp')
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        raise HTTPException(status_code=401, detail='Токен истек')
    
    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=401, detail='Пользователь не найден')

    user = await UserDAO.find_one_or_none_by_id(data_id=int(user_id), db=db)
    if not user:
        raise HTTPException(status_code=401, detail='Пользователь не найден')

    return user  


async def get_current_admin_user(current_user: User =Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail='Недостаточно прав для доступа')
    return current_user


async def get_current_user_optional(
        
        token: str | None = Depends(get_token),
        session: AsyncSession = Depends(get_session)
 
) -> User | None:
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
    except JWTError:
        return None
    
    expire: str = payload.get('exp')
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        return None
    
    user_id: str = payload.get('sub')
    if not user_id:
        return None
    
    user = await UserDAO.find_one_or_none_by_id(data_id=int(user_id), db=session)
    return user