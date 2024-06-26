from typing import Dict

from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from aiogram.dispatcher.handler import CancelHandler
import utils.exception_control
from config import FLOOD_CONTROL, FLOOD_CONTROL_STOP_TIME
from loader import bot, security, dbase


class AccessControlMiddleware(BaseMiddleware):
    """ Класс предварительной обработки входящих сообщений для защиты от нежелательной нагрузки """
    dbase = dbase
    bot = bot
    security = security

    def __init__(self) -> None:
        super().__init__()
        self.sign = self.__class__.__name__ + ': '

    @utils.exception_control.exception_handler_wrapper
    async def on_pre_process_update(self, update: Update, update_data: Dict) -> None:
        update = update.message if update.message else update.callback_query

        user_data = self.manager.storage.data.get(str(update.from_user.id))

        if isinstance(update, CallbackQuery):
            await self.bot.answer_callback_query(callback_query_id=update.id)

        if not await self.security.check_user(update, user_data):
            raise CancelHandler()

        if FLOOD_CONTROL:
            control = await self.security.flood_control(update)
            if control in ['block', 'bad', 'blocked']:
                if control != 'blocked':
                    text = {'block': f'&#129302 Доступ ограничен на {FLOOD_CONTROL_STOP_TIME} секунд',
                            'bad': '&#129302 Не так быстро пожалуйста'}
                    await bot.send_message(chat_id=update.from_user.id, text=text[control])
                raise CancelHandler()
        # data[update.from_user.id] = self.manager.storage.data.get(update.from_user.id)
        import handlers

    @utils.exception_control.exception_handler_wrapper
    async def on_process_update(self, update: Update, update_data: Dict) -> None | Dict:
        pass

    @utils.exception_control.exception_handler_wrapper
    async def on_post_process_update(self, update: Update, post: list, update_data: Dict) -> None:
        pass

    @utils.exception_control.exception_handler_wrapper
    async def on_pre_process_message(self, message: Message, message_data: Dict) -> None:
        pass

    @utils.exception_control.exception_handler_wrapper
    async def on_process_message(self, message: Message, message_data: Dict) -> None:
        pass

    @utils.exception_control.exception_handler_wrapper
    async def on_post_process_message(self, message: Message, post: list, message_data: Dict) -> None:
        pass

    @utils.exception_control.exception_handler_wrapper
    async def on_pre_process_callback_query(self, call: CallbackQuery, callback_data: Dict) -> None:
        pass

    @utils.exception_control.exception_handler_wrapper
    async def on_process_callback_query(self, call: CallbackQuery, callback_data: Dict) -> None:
        pass

    @utils.exception_control.exception_handler_wrapper
    async def on_post_process_callback_query(self, call: CallbackQuery, post: list, callback_data: Dict) -> None:
        pass

