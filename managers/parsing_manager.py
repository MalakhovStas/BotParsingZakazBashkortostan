import json
from datetime import datetime
from zoneinfo import ZoneInfo
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from config import PATH_FILE_INNS


class ParsingManager:

    __instance = None
    def_url = "https://api-zakaz.bashkortostan.ru/apifront/purchases?filter={cust}&status=1"
    link_url = 'https://zakaz.bashkortostan.ru/purchases/grouped/fl44/item/{ID}/view'
    def_headers = {
        "Accept": "application/json",
        "Origin": "https://zakaz.bashkortostan.ru",
        "Referer": "https://zakaz.bashkortostan.ru/",
    }

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, dbase, rm, bot, logger):
        self.dbase = dbase
        self.rm = rm
        self.bot = bot
        self.logger = logger
        self.sign = self.__class__.__name__ + ': '

    async def start_parsing(self):
        for inn in await self.get_inn_list():
            customer = f"{'{'}%22customer%22:%22{inn}%22{'}'}"
            url = self.def_url.format(cust=customer)
            if data := await self.rm(url=url, headers=self.def_headers, method='get'):
                if data.get('data'):
                    await self.mailing(data.get('data')[0])

    async def get_inn_list(self):
        with open(PATH_FILE_INNS, 'r') as file:
            result = json.load(file)
        return result

    async def update_inn_list_file(self, data):
        with open(PATH_FILE_INNS, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    async def mailing(self, data):
        users = await self.dbase.get_all_users(id_only=True, not_ban=True)
        for user in users:
            start_date = datetime.strftime(
                datetime.strptime(data.get('purchase_start'), '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(
                    tz=ZoneInfo('Europe/Moscow')), '%m/%d %H:%M')
            end_date = datetime.strftime(
                datetime.strptime(data.get('purchase_end'), '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(
                    tz=ZoneInfo('Europe/Moscow')), '%m/%d %H:%M')

            result = f"<i>{self.def_headers.get('Origin')}</i>\n" \
                     f"<b>Новый заказ</b>: {data.get('reg_number')}\n" \
                     f"<b>От</b>: {data.get('organization')}\n" \
                     f"<b>Создан</b>: {start_date}\n" \
                     f"<b>Срок сбора</b>: {end_date}"
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(text='Открыть', url=self.link_url.format(ID=data.get("id"))))
            try:
                await self.bot.send_message(chat_id=user.user_id, text=result, reply_markup=keyboard,
                                            disable_web_page_preview=True, parse_mode='HTML')
            except Exception as exc:
                self.logger.warning(self.sign + f'{exc=}')
