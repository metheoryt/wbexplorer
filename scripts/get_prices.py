from pathlib import Path

import pandas as pd

from wbexplorer.client import Client

wb = Client(
    destination=123585476  # г Пушкино, Октябрьская Улица 51а
)

def get_prices(filename: Path):

    df = pd.read_excel(filename)
    df['Total price'] = ''

    # collect articuls
    articul_price = {}
    for row_i, row in df.iterrows():
        try:
            articul = int(row['Артикул WB'])
        except Exception:
            print('empty articul value in row', row_i)
            continue
        articul_price[int(articul)] = '-'

    items = wb.details_many(list(articul_price.keys()))

    # map prices to articuls
    for item in items:
        articul_price[item.id] = item.variants[0].prices.total

    # write prices to a table
    for row_i, row in df.iterrows():
        try:
            articul = int(row['Артикул WB'])
        except Exception:
            continue

        df.loc[row_i, 'Total price'] = articul_price[articul]

    new_filename = Path(f'{filename.stem}-finished{filename.suffix}')
    df.to_excel(new_filename, index=False)
    return new_filename


# new_filename = Path(f'{filename.stem}-finished{filename.suffix}')
    # df.to_excel(new_filename, index=False)
    # return new_filename



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
    new = get_prices(args.filename)
    print('Готово! Новый файл', new)
