from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, TIMESTAMP, ForeignKey, text
from app.database.db import Base
from pydantic import EmailStr


class Role(Base):
    name: Mapped[str] = mapped_column(String, unique=True)
    users: Mapped[list['User']] = relationship(back_populates='roles')


class User(Base):
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    first_name: Mapped[str]
    last_name: Mapped[str]
    
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id'), default=1, server_default=text('1'))
    roles: Mapped['Role'] = relationship('Role', back_populates='users', lazy='joined')

