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
        await self.dbase.update_last_parse_time()

    async def get_inn_list(self):
        with open(PATH_FILE_INNS, 'r') as file:
            result = json.load(file)
        return result

    async def update_inn_list_file(self, data):
        with open(PATH_FILE_INNS, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    async def mailing(self, data):
        users = await self.dbase.get_all_users(id_only=True, not_ban=True)
        last_parse_tm_from_db = await self.dbase.get_or_create_last_parse_time()
        last_parse_time = datetime.strptime(last_parse_tm_from_db, "%Y-%m-%d %H:%M:%S.%f%z")
        start_date = datetime.strptime(data.get('purchase_start'), '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(
            tz=ZoneInfo('Europe/Moscow'))
        end_date = datetime.strptime(data.get('purchase_end'), '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(
            tz=ZoneInfo('Europe/Moscow'))

        if start_date > last_parse_time:
            for user in users:
                # result = f"<i>{self.def_headers.get('Origin')}</i>\n" \ # верхняя строка со ссылкой на сайт
                result = f"<b>Новый заказ</b>: {data.get('reg_number')}\n" \
                         f"<b>От</b>: {data.get('organization')}\n" \
                         f"<b>Создан</b>: {datetime.strftime(start_date, '%m/%d %H:%M')}\n" \
                         f"<b>Срок сбора</b>: {datetime.strftime(end_date, '%m/%d %H:%M')}"
                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton(text='Открыть', url=self.link_url.format(ID=data.get("id"))))
                try:
                    await self.bot.send_message(chat_id=user.user_id, text=result, reply_markup=keyboard,
                                                disable_web_page_preview=True, parse_mode='HTML')
                except Exception as exc:
                    self.logger.warning(self.sign + f'{exc=}')
