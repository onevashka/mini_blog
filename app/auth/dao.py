from app.base_dao import BaseDAO
from .schemas import User, Role


class UserDAO(BaseDAO):
    model = User


class RoleDAO(BaseDAO):
    model = Role