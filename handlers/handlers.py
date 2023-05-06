from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message, ParseMode
from aiogram.utils.exceptions import MessageToDeleteNotFound, MessageCantBeDeleted, \
    MessageToEditNotFound, MessageCantBeEdited
from utils.exception_control import exception_handler_wrapper
from loader import dp, bot, logger
from config import PARSING_INTERVAL_SECONDS, FACE_BOT


async def delete_message(chat_id, message_id):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except (MessageToDeleteNotFound, MessageCantBeDeleted) as exc:
        logger.warning(f'HANDLERS Error: {chat_id=} | {message_id=} | {exc=}')
        return False
    else:
        return True


async def edit_message(chat_id, message_id):
    try:
        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id)
    except (MessageToEditNotFound, MessageCantBeEdited) as exc:
        logger.warning(f'HANDLERS Error: {chat_id=} | {message_id=} | {exc=}')
        return False
    else:
        return True


@dp.message_handler(state='*')
@exception_handler_wrapper
async def get_message_handler(message: Message, state: FSMContext) -> None:
    """ Обработчик сообщений """
    if message.get_command() == '/start':
        period, unit = PARSING_INTERVAL_SECONDS // 60, 'мин.'
        if period > 60:
            period, unit = period // 60, 'час.'
        text = f'{FACE_BOT}Ваш контакт добавлен в список рассылки уведомлений. ' \
               f'Рассылка данных осуществляется с ' \
               f'периодичностью {period} {unit}, ожидайте.'
        await bot.send_message(chat_id=message.from_user.id, text=text, reply_markup=None, disable_web_page_preview=True)


@dp.callback_query_handler(lambda callback: callback.data, state='*')
@exception_handler_wrapper
async def get_call_handler(call: CallbackQuery, state: FSMContext) -> None:
    """ Обработчик обратного вызова """
    pass
    # sent_message = await bot.send_message(chat_id=call.from_user.id, text='Привет',
    #                                       reply_markup=None, disable_web_page_preview=True)
