from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.auth.schemas import User
from app.auth.auth import get_current_user_optional
from .models import MBlogFullResponse, MBlogNotFind
from .dao import BlogDAO
from app.database.db import get_session


async def get_blog_info(
        
        blog_id: int,
        db: AsyncSession = Depends(get_session),
        user_data: User | None = Depends(get_current_user_optional),

) -> MBlogFullResponse | MBlogNotFind:
    """
    Метод для получения полной информации о блоге.
    Если блог не найден или доступ к нему не предоставлен, возвращается соответствующее сообщение.
    """
    author_id = user_data.id if user_data else None
    return await BlogDAO.get_full_blog_info(db=db, blog_id=blog_id, author_id=author_id)