from fastapi import APIRouter, Depends, HTTPException, Query
from app.auth.schemas import User
from app.auth.auth import get_current_user, get_current_user_optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import get_session
from .dao import *
from sqlalchemy.exc import IdentifierError
from .models import MBlogCreate, MBlogFullResponse, MBlogNotFind
from .services import get_blog_info
from fastapi.responses import JSONResponse


router = APIRouter(prefix='/api', tags=['API'])


@router.post('/add_post', summary="Добавление нового блога с тегами")
async def add_blog(
        add_data: MBlogCreate,
        user_data: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_session)          
                   
):
    blog_dict = add_data.model_dump()
    blog_dict['author'] = user_data.id
    tags = blog_dict.pop('tags', [])

    try:
        blog = await BlogDAO.add(db=db, data=blog_dict)
        blog_id = blog.id

        if tags:
            tags_ids = await TagDAO.add_tags(db=db, tag_names=tags)
            await BlogTagDAO.add_blog_tags(db=db, blog_tag_pairs=[{
                                                                'blog_id': blog_id,
                                                                'tag_id': i
                                                                } for i in tags_ids])
            

            return {'status': 'success', 'message': f'Блог с ID {blog_id} успешно добавлен с тегами.'}
    except IdentifierError as e:
        if "UNIQUE constraint failed" in str(e.orig):
            raise HTTPException(status_code=400,
                                detail="Блог с таким заголовком уже существует.")
        raise HTTPException(status_code=500, detail="Ошибка при добавлении блога.")
    

@router.get('/get_blog/{blog_id}', summary="Получить информацию по блогу")
async def get_blog_endpoint(

    blog_id: int,
    blog_info: MBlogFullResponse | MBlogNotFind = Depends(get_blog_info),

) -> MBlogFullResponse | MBlogNotFind:
    return blog_info


@router.delete('/delete_blog/{blog_id}', summary='Удалить блог')
async def delete_blog(

    blog_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user_optional)

):
    
    result = await BlogDAO.delete_blog(db=db, blog_id=blog_id, author_id=current_user.id)
    if result['status'] == 'error':
        raise HTTPException(status_code=403, detail=result['message'])
    return result


@router.patch('/change_blog_status/{blog_id}', summary="Изменить статус блога")
async def change_blog_status(

    blog_id: int,
    new_status: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user_optional)

):
    result = await BlogDAO.change_blog_status(db=db, blog_id=blog_id, new_status=new_status, author_id=current_user.id)
    if result['status'] == 'error':
        raise HTTPException(status_code=403, detail=result['message'])
    return result


@router.get('/blogs', summary="Получить все блоги в статусе 'publish'")
async def get_blogs_info(
    db: AsyncSession = Depends(get_session),
    author_id: int | None = None,
    tag: str | None = None,
    page: int = Query(1, ge=1, description='Номер страницы'),
    page_size: int = Query(10, ge=10, description='Количество записей на странице'),
):
    try:
        result = await BlogDAO.get_list_blog(db=db, author_id=author_id, tag=tag, page=page, page_size=page_size)
        return result if result['blogs'] else print('dsffdsfdsfdss')
    except Exception as e:
        logger.info(f'Ошибка при получении блогов: {e}')
