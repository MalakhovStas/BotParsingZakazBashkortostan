import asyncio
import json
import random
from typing import Iterable
from zoneinfo import ZoneInfo

import aiohttp
from aiohttp_proxy import ProxyConnector, ProxyType

from config import USE_PROXI, PROXI_FILE, TYPE_PROXI, RM_TIMEOUT


class RequestsManager:

    __instance = None

    content_type = {"Content-Type": "application/json"}
    user_agent = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                                "(KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36;"}

    proxi_types = {'socks5': ProxyType.SOCKS5, 'socks4': ProxyType.SOCKS4,
                   'https': ProxyType.HTTPS, 'http': ProxyType.HTTP}

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, logger):
        self.logger = logger
        self.proxies = self.get_proxies()
        self.sign = self.__class__.__name__ + ': '

    async def __call__(self, url: str, headers: dict | None = None, method: str | None = None,
                       data: dict | list | None = None, list_requests: list | None = None,
                       add_headers: bool = False, step: int = 1, use_proxi: bool = True,
                       post_to_form: bool = False) -> Iterable:
        """ Повторяет запрос/запросы, если сервер ответил error=True """

        if not headers:
            headers = self.content_type | self.user_agent
        elif headers and add_headers:
            headers = self.content_type | self.user_agent | headers

        if not method:
            method = 'get'

        if list_requests:
            result = await self.aio_request_gather(list_requests=list_requests,
                                                   headers=headers,
                                                   method=method,
                                                   data=data,
                                                   use_proxi=use_proxi,
                                                   post_to_form=post_to_form)
        else:
            result = await self.aio_request(
                url=url,
                headers=headers,
                method=method,
                data=data,
                use_proxi=use_proxi,
                post_to_form=post_to_form
            )
        if isinstance(result, dict) and result.get('error'):
            step = step + 1
            text = 'i try again call func aio_request because' if step < 3 else 'brake'
            self.logger.warning(self.sign + f'func __call__ {step=} -> {text} -> '
                                            f'{result.get("error")=} | {str(result)[:100]=}...')
            if step < 3:
                result = await self.__call__(url=url, headers=headers, method=method, data=data,
                                             list_requests=list_requests, add_headers=add_headers,
                                             step=step, use_proxi=use_proxi, post_to_form=post_to_form)
        else:
            self.logger.debug(self.sign + f'{step=} func __call__ return {type(result)=} | {len(result)=}')

        return result

    async def check_proxi(self, ip, port, login, password):
        url = 'https://check-host.net/ip'
        connector = ProxyConnector(
            proxy_type=self.proxi_types.get(TYPE_PROXI.lower()),
            host=ip,
            port=port,
            username=login,
            password=password,
        )

        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                async with session.get(url, ssl=False, timeout=RM_TIMEOUT) as response:
                    if response.content_type in ['text/html', 'text/plain']:
                        result = {'response': await response.text()}
                    else:
                        result = await response.json()
            except Exception as exc:
                result = {'response': exc}

        if result.get('response') == ip:
            self.logger.debug(self.sign + f'GOOD PROXI {ip=}, {port=}, {login=}, {password=}, {TYPE_PROXI=}')
            return True
        else:
            self.logger.warning(self.sign + f'ERROR PROXI {ip=}, {port=}, {login=}, '
                                            f'{password=}, {TYPE_PROXI=} | {result=}')
            return False

    @staticmethod
    def get_proxies() -> list:
        proxies = []
        if USE_PROXI:
            with open(PROXI_FILE, 'r') as file:
                proxies = file.read().splitlines()
        return proxies

    async def check_all_proxies(self):
        """ Проверяет работоспособность всех прокси из файла proxi.txt """
        result = {}
        for proxi in self.proxies:
            ip, port, login, password = await self.get_proxi(proxi)
            if ip and port and login and password:
                result.update({f'{login}:{password}@{ip}:{port}': True})
            else:
                result.update({proxi: False})
        return result

    async def get_proxi(self, check_raw_proxi: str | None = None) -> tuple:
        ip, port, login, password = None, None, None, None

        if USE_PROXI:
            try:
                if not check_raw_proxi:
                    proxi = random.choice(self.proxies)
                else:
                    proxi = check_raw_proxi
                proxi = proxi.replace(' ', '\t')
                ip, port, login, password = proxi.split('\t')
                text = 'CHECK_PROXI' if check_raw_proxi else 'USE PROXI'
                self.logger.debug(self.sign + f'{text} -> {ip=}, {port=}, {login=}, '
                                              f'{password=}, {TYPE_PROXI=}')
                if not await self.check_proxi(ip=ip,  port=port, login=login, password=password):
                    ip, port, login, password = None, None, None, None
            except Exception as exc:
                self.logger.error(self.sign + f'{exc=}')
        return ip, port, login, password

    async def aio_request(self, url, headers, method: str = 'get',
                          data: dict | None = None, use_proxi: bool = True,
                          post_to_form: bool = False) -> dict | list:
        """ Повторяет запрос, если во время выполнения запроса произошло исключение из Exception"""
        step = 1
        result = dict()

        ip, port, login, password = None, None, None, None
        if use_proxi:
            for _ in range(5):
                if not all([ip, port, login, password]):
                    ip, port, login, password = await self.get_proxi()
                else:
                    break

        if post_to_form is False and isinstance(data, (dict, list)):
            data = json.dumps(data)
        elif post_to_form is True and isinstance(data, (dict, list)):
            headers.pop('Content-Type')
        else:
            data = None

        self.logger.debug(self.sign+f'{step=} -> sending request to: '
                                    f'{url=} | {method=} | {str(data)=} | {str(headers)[:100]=}...')
        if ip and port and login and password:
            connector = ProxyConnector(
                proxy_type=self.proxi_types.get(TYPE_PROXI.lower()),
                host=ip,
                port=port,
                username=login,
                password=password,
            )
        else:
            connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
            while step < 4:
                try:
                    if method == 'post':
                        async with session.post(url, data=data, ssl=False, timeout=RM_TIMEOUT) as response:
                            if response.content_type in ['text/html', 'text/plain']:
                                result = {'response': await response.text()}
                            else:
                                result = await response.json()
                    elif method == 'patch':
                        async with session.patch(url, data=data, ssl=False, timeout=RM_TIMEOUT) as response:
                            if response.content_type in ['text/html', 'text/plain']:
                                result = {'response': await response.text()}
                            else:
                                result = await response.json()

                    else:
                        async with session.get(url, ssl=False, timeout=RM_TIMEOUT) as response:
                            if response.content_type in ['text/html', 'text/plain']:
                                result = {'response': await response.text()}
                            else:
                                result = await response.json()

                except Exception as exception:
                    text = f'try again' if step < 3 else 'brake requests return EMPTY DICT'
                    self.logger.warning(self.sign + f'ERROR -> {step=} | {exception=} | '
                                                    f'proxi: {ip, port, login, password} -> {text}')
                    step += 1
                else:
                    break
        self.logger.debug(self.sign + f'{step=} | proxi: {ip, port, login, password} | return={str(result)[:100]}...')
        #TODO нужно доделать
        # if msg := result.get('response'):
        #     if msg.find('Forbidden') != -1:
        #         from utils.admins_send_message import func_admins_message
        #         await func_admins_message(update=update, message=f'⚠ <b>Ошибка парсинга:</b>\n'
        #                                                          f'<b>Ответ севера:</b> Forbidden')
        return result

    async def aio_request_gather(
            self, list_requests, headers, method: str = 'get',
            data: dict | None = None, use_proxi: bool = True, post_to_form: bool = False) -> Iterable:

        if method == 'post':
            task_data = [self.aio_request(url=url, headers=headers, method=method,
                                          data=data, use_proxi=use_proxi, post_to_form=post_to_form) for url in list_requests]
        else:
            task_data = [self.aio_request(url=url, headers=headers, use_proxi=use_proxi,
                                          post_to_form=post_to_form) for url in list_requests]
        list_result = await asyncio.gather(*task_data)
        await asyncio.sleep(0.1)
        return list_result
