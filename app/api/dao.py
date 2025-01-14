from app.base_dao import BaseDAO
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from app.logger import logger
from app.api.schemas import *
from sqlalchemy.orm import joinedload, selectinload
from .models import MBlogFullResponse


class TagDAO(BaseDAO):
    model = Tag

    @classmethod
    async def add_tags(cls, db: AsyncSession, tag_names: List[str]) -> List[int]:
        """
        Метод для добавления тегов в базу данных.
        Принимает список строк (тегов), проверяет, существуют ли они в базе данных,
        добавляет новые и возвращает список ID тегов.

        :param session: Сессия базы данных.
        :param tag_names: Список тегов в нижнем регистре.
        :return: Список ID тегов.
        """

        tag_ids = []
        for tag_name in tag_names:
            tag_name.lower()
            stmt = select(cls.model).filter_by(name=tag_name)
            result = await db.execute(stmt)
            tag = result.scalars().first()

            if tag:
                tag_ids.append(tag.id)
            else:
                new_tag = cls.model(name=tag_name)
                db.add(new_tag)
                try:
                    await db.commit()
                    await db.flush()
                    logger.info(f'Тег "{tag_name}" добавлен в базу данных.')
                    tag_ids.append(new_tag.id)

                except SQLAlchemyError as e:
                    await db.rollback()
                    logger.info(f'Ошибка при добавлении тега "{tag_name}": {e}')
                    raise
        return tag_ids


class BlogDAO(BaseDAO):
    model = Blog

    @classmethod
    async def get_full_blog_info(cls, db: AsyncSession, blog_id: int, author_id: int = None):
        """
        Метод для получения полной информации о блоге, включая данные об авторе и тегах.
        Для опубликованных блогов доступ к информации открыт всем пользователям.
        Для черновиков доступ открыт только автору блога.    
        """

        query = (
            select(cls.model)
            .options(
                
                joinedload(Blog.user),
                selectinload(Blog.tags),

            )
            .filter_by(id=blog_id)
        )

        result = await db.execute(query)
        blog = result.scalar_one_or_none()

        if not blog:
            return {

                'message': f'Блог с ID {blog_id} не найден или у вас нет прав на его просмотр.',
                'status': 'error',      

            }
        
        if blog.status == 'draft' and (author_id != blog.author_id):
            return {

                'message': 'Этот блог находится в статусе черновика, и доступ к нему имеют только авторы.',
                'status': 'error',

            }

        return blog
    
    @classmethod
    async def delete_blog(cls, db: AsyncSession, blog_id: int, author_id: int) -> dict:
        """
        Метод для удаления блога. Удаление возможно только автором блога.

        :param session: Асинхронная сессия SQLAlchemy
        :param blog_id: ID блога
        :param author_id: ID автора, пытающегося удалить блог
        :return: Словарь с результатом операции
        """
        try:
            query = select(cls.model).filter_by(id=blog_id)
            result = await db.execute(query)
            blog = result.scalar_one_or_none()

            if not blog:
                return {
                   'message': f'Блог с ID {blog_id} не найден или у вас нет прав на его удаление.',
                   'status': 'error',
                }

            await db.delete(blog)
            await db.commit()
            await db.flush()

            return {
            'message': f"Блог с ID {blog_id} успешно удален.",
            'status': 'success',
             }
        except SQLAlchemyError as e:
            await db.rollback()
            logger.info(f"Ошибка при удалении блога: {e}")
            raise

    @classmethod
    async def change_blog_status(cls, db: AsyncSession, blog_id: int, new_status: str, author_id: int) -> dict:
        """
        Метод для изменения статуса блога. Изменение возможно только автором блога.

        :param session: Асинхронная сессия SQLAlchemy
        :param blog_id: ID блога
        :param new_status: Новый статус блога ('draft' или 'published')
        :param author_id: ID автора, пытающегося изменить статус
        :return: Словарь с результатом операции
        """
        if new_status not in ['draft', 'published']:
            return {
            'message': "Недопустимый статус. Используйте 'draft' или 'published'.",
            'status': 'error'
            }

        try:
            query = select(cls.model).filter_by(id=blog_id)
            result = await db.execute(query)
            blog = result.scalar_one_or_none()

            if not blog:
                return {
                   'message': f'Блог с ID {blog_id} не найден или у вас нет прав на его изменение статуса.',
                   'status': 'error',
                }
            
            if blog.author != author_id:
                return {
                   'message': 'Этот блог не принадлежит вам, и вы не можете изменить его статус.',
                   'status': 'error',
                }
            
            if blog.status == new_status:
                return {

                    'message': f"Блог с ID {blog_id} уже находится в статусе '{new_status}'.",
                    'status': 'info',
                    'blog_id': blog_id,
                    'current_status': new_status

                }
            
            blog.status = new_status
            await db.commit()

            return {
                'message': f"Блог с ID {blog_id} успешно изменен в статусе '{new_status}'.",
                'status':'success',
                'blog_id': blog_id,
                'current_status': new_status
            }
        except SQLAlchemyError as e:
            await db.rollback()
            logger.info(f"Ошибка при изменении статуса блога: {e}")
            raise


    @classmethod
    async def get_list_blog(cls, db: AsyncSession, author_id: int = None, tag: str = None, page: int = 1, page_size: int = 10):
        
        base_query = select(cls.model).options(

            joinedload(cls.model.user),
            selectinload(cls.model.tags)
        ).filter_by(status='published')

        if author_id is not None:
            base_query = base_query.filter_by(author=author_id)

        if tag:
            base_query = base_query.join(cls.model.tags).filter(cls.model.tags.any(Tag.name.ilike(f"%{tag.lower()}%")))

        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await db.scalar(count_query)

        if not total_result:
            return {

                'page': page,
                'total_page': 0,
                'total_result': 0,
                'blogs': [],

            }

        total_page = (total_result + page_size - 1) // page_size

        offset = (page - 1) * page_size
        paginated_query = base_query.offset(offset).limit(page_size)

        result = await db.execute(paginated_query)
        blogs = result.scalars().all()

        unique_blogs = []
        seen_ids = set()

        for blog in blogs:
            if blog.id not in seen_ids:
                unique_blogs.append(MBlogFullResponse.model_validate(blog))
                seen_ids.add(blog.id)

        filters = []
        if author_id is not None:
            filters.append(f"author_id={author_id}")
        if tag:
            filters.append(f"tag={tag}")
        filter_str = " & ".join(filters) if filters else "no filters"

        logger.info(f"Page {page} fetched with {len(blogs)} blogs, filters: {filter_str}")
        # Формирование результата
        return {
            "page": page,
            "total_page": total_page,
            "total_result": total_result,
            "blogs": unique_blogs
        }


class BlogTagDAO(BaseDAO):
    model = BlogTag


    @classmethod
    async def add_blog_tags(cls, db: AsyncSession, blog_tag_pairs: List[dict]) -> None:
        blog_tag_instances = []
        for pair in blog_tag_pairs:
            blog_id = pair.get('blog_id')
            tag_id = pair.get('tag_id')
            print(blog_id, tag_id)
            if blog_id and tag_id:
                blog_tag = cls.model(blog_id=blog_id, tag_id=tag_id)
                blog_tag_instances.append(blog_tag)
                print(blog_tag)
            else:
                logger.warning(f"Пропущен неверный параметр в паре: {pair}")
        
        print(blog_tag_instances)
        if blog_tag_instances:
            print(blog_tag_instances)
            db.add_all(blog_tag_instances)
            try:
                await db.commit()
                await db.flush()
                logger.info(f"{len(blog_tag_instances)} связок блогов и тегов успешно добавлено.")
            except SQLAlchemyError as e:
                await db.rollback()
                logger.info(f"Ошибка при добавлении связок блогов и тегов: {e}")
                raise
        else:
            logger.warning("Нет валидных данных для добавления в таблицу blog_tags.")

        

    