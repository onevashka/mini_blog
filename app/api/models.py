from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict, computed_field, Field


class BaseModelConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MBlogCreate(BaseModelConfig):
    title: str
    content: str
    short_description: str
    tags: List[str] = []


class UserBase(BaseModelConfig):
    id: int
    first_name: str
    last_name: str


class TagResponse(BaseModelConfig):
    id: int
    name: str


class MBlogFullResponse(BaseModelConfig):
    id: int 
    author: int
    title: str
    content: str
    short_description: str
    created_at: datetime
    status: str
    tags: List[TagResponse]

    user: UserBase = Field(exclude=True)


class MBlogNotFind(BaseModelConfig):
    message: str
    status: str