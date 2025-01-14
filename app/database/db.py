from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncAttrs, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, declared_attr
from app.config import DATABASE_URL
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, func, TIMESTAMP
from datetime import datetime

engine = create_async_engine(DATABASE_URL)

AsyncSession =  async_sessionmaker(bind=engine, expire_on_commit=False)


def get_session():
    session = AsyncSession()
    try:
        yield session
    except Exception as e:
        raise e
    finally:
        session.close()


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + 's'