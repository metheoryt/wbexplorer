import time
from collections import defaultdict
from pathlib import Path

import pandas as pd

from wbexplorer.client import Client
from wbexplorer.wbtypes import WBItem

_SEARCH_CACHE = defaultdict(list)


wb = Client(
    destination=123585476  # г Пушкино, Октябрьская Улица 51а
)

def get_search_results(query: str, page: int) -> list[WBItem]:
    """
    Кэшируем результаты запроса, для стабильности и скорости.
    Боремся с мусорной выдачей несколькими попытками перезапроса.
    """
    if (query, page) in _SEARCH_CACHE:
        print('cache hit')
        return _SEARCH_CACHE[(query, page)]

    results = []
    for i in range(5):  # 5 попыток
        if i:
            print(f'sleeping {i*2} seconds before querying wb')
            time.sleep(i*2)
        try:
            results = wb.search(query, page)
        except KeyError:
            print(f'query "{query}", page {page}, try #{i+1}, failed to get results')
            continue
        else:
            _SEARCH_CACHE[(query, page)] = results
            print(f'query "{query}", page {page}, try #{i+1}, {len(results)} results')
            break
    return results


def locate_item_position(query: str, item_id: int) -> tuple[int, WBItem] | tuple[None, None]:
    """
    Ищем товар на первых 3 страницах. Если не найден - возвращаем (None, None).
    На странице - по 100 товаров.
    """
    for page in range(3):
        results = get_search_results(query=query, page=page + 1)

        for i, item in enumerate(results):
            if item.id == item_id:
                return (i + 1) + (page * 100), item

        if 0 < len(results) < 100:
            # это последняя страница
            break

    return None, None


def search_positions(filename: Path):

    df = pd.read_excel(filename)
    df['Позиция'] = ''

    for row_i, row in df.iterrows():
        search_query = row['Ссылка']
        if not search_query.strip():
            print('empty value for query in row', row_i)
            continue
        item_pos, item = locate_item_position(search_query, int(row['Артикул WB']))
        df.loc[row_i, 'Позиция'] = str(item_pos) if item_pos else '300+'
        if item:
            df.loc[row_i, 'Цена total'] = item.variants[0].prices.total

    new_filename = Path(f'{filename.stem}-finished{filename.suffix}')
    df.to_excel(new_filename, index=False)
    return new_filename


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description="""\
Проставить для артикулов порядковый номер в выдаче в поиске в Москве. 
Требуемые столбцы исходной таблицы:
Ссылка - ссылка на поиск.
Артикул - номер товара.
"""
    )
    parser.add_argument("filename", type=Path, help="Путь к файлу excel таблицы.")
    args = parser.parse_args()
    new = search_positions(args.filename)
    print('Готово! Новый файл', new)
