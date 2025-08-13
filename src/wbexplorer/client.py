import datetime
import json
from decimal import Decimal
from itertools import batched
import requests
from fake_useragent import FakeUserAgent

from .wbtypes import WBItem


BASE_URL = 'https://www.wildberries.ru/'
SEARCH_URL = 'https://search.wb.ru/exactmatch/sng/common/v7/search'
DETAILS_URL = 'https://card.wb.ru/cards/v2/detail'


class Client:
    def __init__(self, destination: int = -1292286):
        """
        :param destination: delivery destination, defaults to some in Moscow.
        """
        self.dest = destination
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': FakeUserAgent().getChrome['useragent']})
        # check connection, get any cookies required
        # UPD seems that this is not required anymore
        # r = self.session.get(BASE_URL)
        # r.raise_for_status()

    def search(self, query: str, page: int = 1) -> list[WBItem]:
        """
        Search for items.
        :param query: search query
        :param page: page number
        :return: list of WBItem objects.
        """
        response = self.session.get(
            SEARCH_URL,
            params={
                'spp': 30,
                'sort': 'popular',
                'resultset': 'catalog',
                'query': query,
                'dest': self.dest,
                'curr': 'rub',
                'appType': 1,
                'ab_testing': 'false',
                'suppressSpellcheck': 'false',
                'page': page,
            },
        )
        items = []
        rs = response.json()
        if not rs.get('data', {}).get('products'):
            print('search response is empty:', rs)
            return items

        for i, v in enumerate(response.json()['data']['products']):
            try:
                item = WBItem.from_dict(v)
            except Exception as e:
                print(f'cannot parse WBItem at #{i}, {type(e).__name__} {e}:', json.dumps(v))
                raise
            items.append(item)
        return items

    @staticmethod
    def basket_vol_part(item_id: int) -> tuple[str, int, int]:
        short_id = item_id // 100_000
        if short_id >= 10_000:
            raise ValueError('short_id is too big')
        # [)
        baskets = [0, 144, 288, 432, 720, 1008, 1062, 1116, 1170, 1314, 1602, 1656, 1920, 2046, 2190, 2406, 10_000]
        for i in range(1, len(baskets)):
            if baskets[i - 1] <= short_id < baskets[i]:
                return f'{i:02}', short_id, item_id // 1000

    def price_history(self, item_id: int) -> list[tuple[datetime.date, Decimal]]:
        basket, vol, part = self.basket_vol_part(item_id)
        response = self.session.get(
            f'https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{item_id}/info/price-history.json'
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
        print('price history for', item_id, ':', hist)
        return hist

    def details_many(self, item_ids: list[int]) -> list[WBItem]:
        many = []
        for batch in batched(item_ids, 20):
            # max 10 items in one query
            response = self.session.get(DETAILS_URL, params={
                'appType': 1,
                'curr': 'rub',
                'dest': self.dest,
                'spp': 30,
                'hide_dtype': 10,
                'ab_testing': False,
                'nm': ';'.join(map(str, batch)),
            })
            response.raise_for_status()
            data = response.json()
            print(data)
            many.extend(list(map(WBItem.from_dict, data['data']['products'])))
        return many

    def details(self, item_id: int) -> WBItem:
        return self.details_many([item_id])[0]
