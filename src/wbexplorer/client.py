import datetime
import json
from decimal import Decimal

import requests
from fake_useragent import FakeUserAgent

from .wbtypes import WBItem


BASE_URL = 'https://www.wildberries.ru/'
SEARCH_URL = 'https://search.wb.ru/exactmatch/sng/common/v7/search'


class Client:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': FakeUserAgent().getChrome['useragent']})
        # check connection, get any cookies required
        r = self.session.get(BASE_URL)
        r.raise_for_status()

    async def search(self, query: str, dest: int) -> list[WBItem]:
        """
        Search for items.
        :param query: search query
        :param dest: search destination, e.g. 123585479 for one in Moscow
        :return: list of WBItem objects.
        """
        response = self.session.get(
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
        )
        items = []
        for v in response.json()['data']['products']:
            try:
                item = WBItem.from_dict(v)
            except Exception as e:
                print(f'cannot parse into wb item, {e}:', json.dumps(v))
                continue
            items.append(item)
        return items

    async def price_history(self, item_id: int) -> list[tuple[datetime.date, Decimal]]:
        vol = str(item_id)[:4]
        part = str(item_id)[:6]

        response = self.session.get(
            f'https://basket-{10}.wbbasket.ru/vol{vol}/part{part}/{item_id}/info/price-history.json'
        )
        response.raise_for_status()
        
        hist = []
        for v in response.json():
            hist.append(
                (
                    datetime.datetime.fromtimestamp(v['dt']).date(),
                    Decimal(v['price']['RUB']) / Decimal(100),
                )
            )
        return hist
