from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt


pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_verify_password(plain_password: str, hashed_password: str) -> str:
    return pwd_context.verify(plain_password, hashed_password)


def get_access_token(data: dict) -> bool:
    encode_data = data.copy()
