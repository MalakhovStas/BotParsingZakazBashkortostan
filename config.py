import os
from dotenv import load_dotenv, find_dotenv

if not find_dotenv():
    exit('Переменные окружения не загружены т.к отсутствует файл .env\n'
         'Необходимо верно заполнить данные в файле .env.template и переименовать его в .env')
else:
    load_dotenv()

""" Список администраторов и ссылка на чат поддержки """
ADMINS = os.getenv('ADMINS').split(', ') if os.getenv('ADMINS') else tuple()
TECH_ADMINS = os.getenv('TECH_ADMINS').split(', ') if os.getenv('TECH_ADMINS') else tuple()
SUPPORT = os.getenv('SUPPORT')

DEFAULT_COMMANDS = (
    ('start', 'Запустить бота'),
)

""" Количество перезапусков бота в случае падения """
MAX_RESTART_BOT = 3

""" Токен и имя телеграм бота """
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_NIKNAME = os.getenv('BOT_NIKNAME')
FACE_BOT = '🤖 \t'

""" Конфигурация базы данных """
DATABASE_CONFIG = ('sqlite', {'database': 'database/database.db',
                              'pragmas': (('cache_size', -1024 * 64),
                                          ('journal_mode', 'wal'), ('foreign_keys', 1))})

""" Конфигурация логирования """
errors_format = '{time:DD-MM-YYYY at HH:mm:ss} | {level: <8} | {file: ^20} | {message}'
debug_format = '{time:DD-MM-YYYY at HH:mm:ss} | {level: <8} | file: {file: ^30} | ' \
               'func: {function: ^30} | line: {line: >3} | message: {message}'

logger_common_args = {
    'diagnose': True,
    'backtrace': False,
    'rotation': '10 Mb',
    'retention': 1,
    'compression': 'zip'
}

PATH_FILE_DEBUG_LOGS = 'logs/debug.log'
PATH_FILE_ERRORS_LOGS = 'logs/errors.log'

LOGGER_DEBUG = {'sink': PATH_FILE_DEBUG_LOGS, 'level': 'DEBUG', 'format': debug_format} | logger_common_args
LOGGER_ERRORS = {'sink': PATH_FILE_ERRORS_LOGS, 'level': 'WARNING', 'format': errors_format} | logger_common_args

""" Конфигурация прокси """
USE_PROXI = False
PROXI_FILE = ''
TYPE_PROXI = ''
RM_TIMEOUT = 20

""" Настройки регулярности парсинга """
# PARSING_INTERVAL_SECONDS = 60*60*12  # каждые 12 часов
PARSING_INTERVAL_SECONDS = 60*15  # каждые 15 минут

""" Путь к файлу с ИНН """
PATH_FILE_INNS = os.path.abspath('inns.json')

""" Включение / отключение механизма защиты от флуда """
FLOOD_CONTROL = True

""" Время между сообщениями от пользователя для защиты от флуда в секундах """
FLOOD_CONTROL_TIME = 0.3

""" Количество предупреждений перед блокировкой для защиты от флуда"""
FLOOD_CONTROL_NUM_ALERTS = 10

""" Время остановки обслуживания пользователя для защиты от флуда в секундах """
FLOOD_CONTROL_STOP_TIME = 60

try:
    from local_settings import *
except ImportError:
    pass