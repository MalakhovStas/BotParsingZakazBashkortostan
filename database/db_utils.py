from datetime import datetime

from peewee import *
from peewee import ModelBase
from playhouse.sqlite_ext import SqliteDatabase

from config import DATABASE_CONFIG

databases = {
    'sqlite': SqliteDatabase,
    'postgres': PostgresqlDatabase,
    'mysql': MySQLDatabase
}

db: SqliteDatabase | PostgresqlDatabase | MySQLDatabase = databases[DATABASE_CONFIG[0]](**DATABASE_CONFIG[1])


class User(Model):
    user_id = IntegerField(primary_key=True, unique=True)
    username = CharField(null=True)
    first_name = CharField(null=True)
    last_name = CharField(null=True)

    date_join = DateTimeField(default=datetime.now(), null=False)  # Два поля для одного и того-же
    access = CharField(default='allowed', null=False)  # Режим доступа к боту
    start_time_limited = IntegerField(null=True)  # Время начала блокировки пользователя используется в middleware
    position = CharField(null=False, default='user')  # Позиция - user | admin
    password = CharField(null=True)  # Пароль обязателен для admin
    ban_from_user = BooleanField(null=False, default=False)  # Забанил ли пользователь бота

    class Meta:
        database = db
        order_by = 'date_join'
        db_table = 'users'


class Tables:
    users = User

    @classmethod
    def all_tables(cls):
        return [value for value in cls.__dict__.values() if isinstance(value, ModelBase)]
