import asyncio
import datetime
import json
from decimal import Decimal

import aiohttp
from aiohttp import CookieJar
from fake_useragent import FakeUserAgent

from wbtypes import WBItem


BASE_URL = 'https://www.wildberries.ru/'
SEARCH_URL = 'https://search.wb.ru/exactmatch/sng/common/v7/search'


class WBExplorerClient:
    def __init__(self):
        self.cookie_jar = CookieJar()
        self.ua = FakeUserAgent().getChrome['useragent']

    @classmethod
    async def new(cls):
        obj = WBExplorerClient()
        await obj._warmup()
        return obj

    async def _warmup(self):
        """Make a request to wildberries to obtain cookies etc."""
        async with self.s() as s:
            async with s.get(BASE_URL) as r:
                r.raise_for_status()
                await r.text()

    def s(self, **kwargs):
        return aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False),
            cookie_jar=self.cookie_jar,
            headers={'User-Agent': self.ua},
            **kwargs,
        )

    async def search(self, query: str, dest: int) -> list[WBItem]:
        """
        Search for items.
        :param query: search query
        :param dest: search destination, e.g. 123585479 for one in Moscow
        :return: list of WBItem objects.
        """
        async with self.s() as session:
            async with session.get(
                SEARCH_URL,
                params={
                    'spp': 30,
                    'sort': 'popular',
                    'resultset': 'catalog',
                    'query': query,
                    'dest': dest,
                    'curr': 'rub',
                    'appType': 1,
                    'ab_testing': 'false',
                    'suppressSpellcheck': 'false',
                },
            ) as response:
                rs = await response.json(content_type='text/plain')
                items = []
                for v in rs['data']['products']:
                    try:
                        item = WBItem.from_dict(v)
                    except Exception as e:
                        print(f'cannot parse into wb item, {e}:', json.dumps(v))
                        continue
                    items.append(item)
                return items

    async def price_history(self, item_id: int) -> list[tuple[datetime.date, Decimal]]:
        basket_number = 10  # basket identification doesn't work, need to deobfuscate js
        for vol_len, part_len in ((4, 6),):  # same for vol/part lengths
            await asyncio.sleep(1)
            vol = str(item_id)[:vol_len]
            part = str(item_id)[:part_len]

            async with self.s() as session:
                async with session.get(
                    f'https://basket-{basket_number}.wbbasket.ru/vol{vol}/part{part}/{item_id}/info/price-history.json'
                ) as response:
                    try:
                        response.raise_for_status()
                    except Exception as e:
                        print(e)
                        continue

                    data = await response.json()

            hist = []
            for v in data:
                hist.append(
                    (
                        datetime.datetime.fromtimestamp(v['dt']).date(),
                        Decimal(v['price']['RUB']) / Decimal(100),
                    )
                )
            return hist
