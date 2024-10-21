from pathlib import Path

from wbexplorer.client import Client
from wbexplorer.wbtypes import WBItem
import pandas as pd
from urllib.parse import urlparse, parse_qs
import time
from collections import defaultdict

_SEARCH_CACHE = defaultdict(list)


wb = Client(
    destination=123585476  # г Пушкино, Октябрьская Улица 51а
)


def get_results(query: str, page: int) -> list[WBItem]:
    """
    Кэшируем результаты запроса, для стабильности и скорости.
    Боремся с мусорной выдачей несколькими попытками перезапроса.
    """
    if (query, page) in _SEARCH_CACHE:
        print('cache hit')
        return _SEARCH_CACHE[(query, page)]

    for i in range(1, 4):
        print(f'sleeping {i * 2} seconds before querying wb')
        time.sleep(2 * i)
        results = wb.search(query, page)
        if not results:
            print(f'try #{i}, no results')
            continue
        else:
            print(f'try #{i}, found results')
            _SEARCH_CACHE[(query, page)] = results
        return results


def locate_item_position(query: str, item_id: int) -> tuple[int, WBItem] | tuple[None, None]:
    """Ищем товар на первых 3 страницах. Если не найден - возвращаем None."""
    for page in range(1, 4):
        for i, item in enumerate(get_results(query=query, page=page)):
            if item.id == item_id:
                return (i+1) * page, item
    return None, None


def search_positions(filename: Path):

    df = pd.read_excel(filename)

    for row_i, row in df.iterrows():
        query_params = parse_qs(urlparse(row['Ссылка']).query)
        search_term = query_params.get('search', [None])[0]

        item_pos, item = locate_item_position(search_term, int(row['Артикул']))
        if item_pos is not None:
            df.loc[row_i, 'Позиция'] = item_pos
            df.loc[row_i, 'Цена total'] = item.variants[0].prices.total

            # последняя цена
            # dt, price = wb.price_history(item.id)[-1]
            # df.loc[row_i, 'Дата последней цены'] = dt.strftime('%Y-%m-%d')
            # df.loc[row_i, 'Последняя цена'] = price

    new_filename = Path(f'{filename.stem}-finished{filename.suffix}')
    df.to_excel(new_filename, index=False)
    return new_filename

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description="""\
Проставить для артикулов порядковый номер в выдаче в поиске в Москве. 
Столбцы:
Ссылка - ссылка на поиск.
Артикул - номер товара.
"""
    )
    parser.add_argument("filename", type=Path, help="Путь к файлу excel таблицы.")
    args = parser.parse_args()
    new = search_positions(args.filename)
    print('Готово! Новый файл', new)
