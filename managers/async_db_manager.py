import functools
from datetime import datetime
from types import FunctionType
from typing import Any, Callable

from aiogram.types import Message, CallbackQuery
from loguru import logger

from config import ADMINS, TECH_ADMINS
from database.db_utils import Tables, db

"""Все таблицы создаются тут - потому, что таблицы должны создаваться раньше чем экземпляр класса DBManager, иначе 
будут ошибки при создании экземпляров классов кнопок и сообщений"""
db.create_tables(Tables.all_tables())


class DBManager:
    """ Класс Singleton надстройка над ORM "peewee" для соблюдения принципа DRY и вынесения логики сохранения данных """
    point_db_connection = db
    tables = Tables

    __instance = None
    sign = None
    logger = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.sign = cls.__name__ + ': '
            cls.logger = logger
            cls.decorate_methods()
        return cls.__instance

    def __init__(self):
        pass

    @staticmethod
    def db_connector(method: Callable) -> Callable:
        @functools.wraps(method)
        async def wrapper(*args, **kwargs) -> Any:
            with DBManager.point_db_connection:
                result = await method(*args, **kwargs)
            return result
        return wrapper

    @classmethod
    def decorate_methods(cls):
        for attr_name in cls.__dict__:
            if not attr_name.startswith('__') and attr_name not in ['db_connector', 'decorate_methods']:
                method = cls.__getattribute__(cls, attr_name)
                if type(method) is FunctionType:
                    cls.logger.debug(cls.sign + f'decorate_methods -> db_connector wrapper -> method: {attr_name}')
                    setattr(cls, attr_name, cls.db_connector(method))

    async def get_or_create_user(self, update: Message | CallbackQuery) -> tuple[tuple, bool | int]:
        """ Если user_id не найден в таблице Users -> создаёт новуе записи в
            таблице Users по ключу user_id """
        fact_create_and_num_users = False
        admin = True if update.from_user.id in set(tuple(map(
            int, ADMINS)) if ADMINS else tuple() + tuple(map(int, TECH_ADMINS)) if TECH_ADMINS else tuple()) else False

        with self.point_db_connection:
            user, fact_create = self.tables.users.get_or_create(user_id=update.from_user.id)
            if fact_create:
                fact_create_and_num_users = self.tables.users.select().count()
                user.user_id = int(update.from_user.id)
                user.username = update.from_user.username
                user.first_name = update.from_user.first_name
                user.last_name = update.from_user.last_name
                user.position = "admin" if admin else "user"
                user.password = "admin" if admin else None
                user.save()

        text = 'created new user' if fact_create else 'get user'
        self.logger.debug(self.sign + f' {text.upper()}: {user.username=} | {user.user_id=}')
        return user, fact_create_and_num_users

    async def get_all_users(self, id_only: bool = False, not_ban: bool = False) -> tuple:
        if not_ban and id_only:
            result = tuple(self.tables.users.select(
                self.tables.users.user_id).where(self.tables.users.ban_from_user == 0))
            self.logger.debug(self.sign + f'func get_all_users -> selected all users_id WHERE ban != ban '
                                          f'num: {len(result) if result else None}')

        elif id_only:
            result = tuple(self.tables.users.select(self.tables.users.user_id))
            self.logger.debug(self.sign + f'func get_all_users -> selected all users_id '
                                          f'num: {len(result) if result else None}')

        else:
            result = self.tables.users.select()
            self.logger.debug(self.sign + f'func get_all_users -> selected all users fields '
                                          f'num: {len(result) if result else None}')

        return result

    async def update_user_access(self, user_id: str | int, block: bool = False) -> bool | tuple:
        user = self.tables.users.get_or_none(user_id=user_id)
        if not user:
            return False
        if block:
            user.access = 'block'
        else:
            user.access = 'allowed'
        user.save()
        self.logger.debug(self.sign + f'func update_user_access -> {"BLOCK" if block else "ALLOWED"} '
                                      f'| user_id: {user_id}')
        return True, user.username

    async def update_ban_from_user(self, update, ban_from_user: bool = False) -> bool | tuple:
        user: Tables.users = self.tables.users.get_or_none(user_id=update.from_user.id)
        if not user:
            return False
        user.ban_from_user = ban_from_user
        user.save()
        self.logger.debug(self.sign + f'func update_ban_from_user -> user: {user.username} | '
                                      f'user_id: {update.from_user.id} | ban: {ban_from_user}')
        return True, user.username

    async def count_users(self, all_users: bool = False, register: bool = False,  date: datetime | None = None) -> str:
        if all_users:
            nums = self.tables.users.select().count()
            self.logger.debug(self.sign + f'func count_users -> all users {nums}')

        elif register:
            nums = self.tables.users.select().wheere(self.tables.users.date_join == date).count()
            self.logger.debug(self.sign + f'func count_users -> num users: {nums} WHERE date_join == date: {date}')

        else:
            nums = self.tables.users.select().where(self.tables.users.date_last_request >= date).count()
            self.logger.debug(self.sign + f'func count_users -> num users: {nums} '
                                          f'WHERE date_last_request == date: {date}')

        return nums

    async def select_all_contacts_users(self) -> tuple:
        users = self.tables.users.select(
            self.tables.users.user_id,
            self.tables.users.first_name,
            self.tables.users.username,
            self.tables.users.date_join,
            self.tables.users.ban_from_user)
        if not users:
            self.logger.error(self.sign + f'BAD -> NOT users in DB')
        else:
            self.logger.debug(self.sign + f'OK -> SELECT all contacts users -> return -> {len(users)} users contacts')

        return users

    async def select_password(self, user_id: int) -> str:
        user = self.tables.users.select(self.tables.users.password).where(self.tables.users.user_id == user_id).get()
        self.logger.debug(self.sign + f'func select_password password -> len password {len(user.password)}')
        return user.password
