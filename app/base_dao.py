from sqlalchemy.ext.asyncio import AsyncSession
from typing import Generic, TypeVar, List, Any
from .database.db import Base
from .logger import logger
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from fastapi import HTTPException


T = TypeVar('T', bound=Base)


class BaseDAO(Generic[T]):
    model: type[T]


    @classmethod
    async def find_one_or_none_by_id(cls, data_id: int, db: AsyncSession):
        logger.info(f'Поиск {cls.model.__name__} с ID: {data_id}')
        try:
            query = select(cls.model).filter_by(id=data_id)
            result = await db.execute(query)
            record = result.scalar_one_or_none()
            if record:
                logger.info(f'Найден {cls.model.__name__} с ID: {data_id}')
            else:
                logger.info(f'Не найден {cls.model.__name__} с ID: {data_id}')
            return record
        except SQLAlchemyError as e:
            logger.error(f'Ошибка при поиске {cls.model.__name__} с ID: {data_id}. Error: {e}')
            raise
        

    @classmethod
    async def find_one_or_none(cls, filters: dict, db: AsyncSession):
        logger.info(f'Поиск одной записи {cls.model.__name__} по фильтрам: {filters}')
        try:
            query = select(cls.model).filter_by(**filters)
            result = await db.execute(query)
            record = result.scalar_one_or_none()
            if record:
                logger.info(f'Найдена одна запись {cls.model.__name__} по фильтрам: {filters}')
            else:
                logger.info(f'Не найдена одна запись {cls.model.__name__} по фильтрам: {filters}')
            return record
        except SQLAlchemyError as e:
            logger.error(f'Ошибка при поиске одной записи {cls.model.__name__} по фильтрам: {filters}. Error: {e}')
            raise
        
    
    @classmethod
    async def find_all(cls, filters: BaseModel | None, db: AsyncSession):
        if filters:
            filters_dict = filters.model_dump(exclude_unset=True)
        else:
            logger.info('Ничего не предали!')
            raise HTTPException(status_code=400, detail='Ничего не передали')

        logger.info(f'Поиск всех записей {cls.model.__name__} по фильтрам: {filters_dict}')
        try:
            query = select(cls.model).filter_by(**filters_dict)
            result = await db.execute(query)
            records = result.scalars().all()
            logger.info(f'Найдены всего записи {len(records)} по фильтрам: {filters_dict}')
            return records
        except SQLAlchemyError as e:
            logger.error(f'Ошибка при поиске всех записей {cls.model.__name__} по фильтрам: {filters_dict}. Error: {e}')
            raise


    @classmethod
    async def add(cls, data: dict, db: AsyncSession):
        logger.info(f'Добавление записи {cls.model.__name__} с параметрами: {data}')
        new_instance = cls.model(**data)
        try:
            db.add(new_instance)
            await db.flush()
            await db.commit()
            logger.info(f'Запись {cls.model.__name__} успешно добавлена.')
        except SQLAlchemyError as e:
            await db.rollback()
            logger.info(f'Ошибка при добавлении записи: {e}')
            raise
        return new_instance
    

    @classmethod
    async def add_many(cls, data: List[BaseModel], db: AsyncSession):
        data_dict = [item.model_dump(exclude_unset=True) for item in data]
        logger.info(f'Добавление множества записей {cls.model.__name__} с параметрами: {data_dict}')
        new_instances = [cls.model(**values) for values in data_dict]
        try:
            db.add_all(new_instances)
            await db.flush()
            await db.commit()
            logger.info(f'Записи {cls.model.__name__} успешно добавлены.')
            return new_instances
        except SQLAlchemyError as e:
            await db.rollback()
            logger.info(f'Ошибка при добавлении множества записей: {e}')
            raise

    
    @classmethod
    async def update(cls, filters: BaseModel, data: BaseModel, db: AsyncSession):
        filter_dict = filters.model_dump(exclude_unset=True)
        data_dict = data.model_dump(exclude_unset=True)
        logger.info(f'Обновление записей {cls.model.__name__} по фильтрам: {filter_dict} с новыми данными: {data_dict}')
        query = (
            
            update(cls.model)
            .where(*[getattr(cls.model, k) == v for k, v in filter_dict.items()])
            .values(**data_dict)
            .execution_options(synchronize_session=True)

        )
        try:
            result = await db.execute(query)
            await db.flush()
            await db.commit()
            logger.info(f"Обновлено {result.rowcount} записей.")
            return result.rowcount
        except SQLAlchemyError as e:
            await db.rollback()
            logger.info(f"Ошибка при обновлении записей: {e}")
            raise


    @classmethod
    async def delete(cls, filters: BaseModel, db: AsyncSession):
        filter_dict = filters.model_dump(exclude_unset=True)
        logger.info(f'Удаление записей {cls.model.__name__} по фильтрам: {filter_dict}')
        if not filter_dict:
            logger.info('Ничего не предали!')
            raise ValueError('Ничего не передали')
        query = delete(cls.model).filter_by(**filter_dict)
        try:
            result = await db.execute(query)
            await db.flush()
            await db.commit()
            logger.info(f'Удалено {result.rowcount} записей.')
            return result.rowcount
        except SQLAlchemyError as e:
            await db.rollback()
            logger.info(f'Ошибка при удалении записей: {e}')
            raise


    @classmethod
    async def count(cls, filters: BaseModel, db: AsyncSession):
        filters_dict = filters.model_dump(exclude_unset=True)
        logger.info(f'Подсчет количества записей {cls.model.__name__} по фильтрам: {filters_dict}')
        try:
            query = select(func.count(cls.model.id).filter(**filters_dict))
            result = await db.execute(query)
            count = result.scalar()
            logger.info(f'Найдено {count} записей.')
            return count
        except SQLAlchemyError as e:
            logger.error(f'Ошибка при подсчете количества записей: {e}')
            raise

    
    @classmethod
    async def paginate(cls, filters: BaseModel, db: AsyncSession, page: int = 1, page_size: int = 10):
        filters_dict = filters.model_dump(exclude_unset=True) if filters else {}
        logger.info(f'Пагинация записей {cls.model.__name__} по фильтрам: {filters_dict} на странице {page} со смещением {page_size}')
        try:
            query = select(cls.model).filter_by(**filters_dict)
            result = await db.execute(query.offset(page - 1) * page_size).limit(page_size)
            records = result.scalars().all()
            logger.info(f'Найдено {len(records)} записей.')
            return records
        except SQLAlchemyError as e:
            logger.error(f'Ошибка при пагинации записей: {e}')
            raise


    @classmethod
    async def find_by_ids(cls, ids: List[int], db: AsyncSession) -> List[Any]:
        logger.info(f"Поиск записей {cls.model.__name__} по списку ID: {ids}")
        try:
            query = select(cls.model).filter(cls.model.id.in_(ids))
            result = await db.execute(query)
            records = result.scalars().all()
            logger.info(f"Найдено {len(records)} записей по списку ID.")
            return records
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске записей по списку ID: {e}")
            raise
