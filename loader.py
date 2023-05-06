from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from loguru import logger

from config import BOT_TOKEN, LOGGER_ERRORS, LOGGER_DEBUG, PARSING_INTERVAL_SECONDS
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from managers.requests_manager import RequestsManager
from managers.parsing_manager import ParsingManager
from managers.async_db_manager import DBManager
from managers.security_manager import SecurityManager

""" Модуль загрузки основных инструментов приложения """

logger.add(**LOGGER_ERRORS)
logger.add(**LOGGER_DEBUG)

bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)
dbase = DBManager()
security = SecurityManager(dbase=dbase, logger=logger)
rm = RequestsManager(logger=logger)
scheduler = AsyncIOScheduler()

pm = ParsingManager(dbase=dbase, rm=rm, bot=bot, logger=logger)

scheduler.add_job(pm.start_parsing, trigger='interval', seconds=PARSING_INTERVAL_SECONDS)
