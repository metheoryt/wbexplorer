import asyncio
from client import WBExplorerClient


async def main():
    c = await WBExplorerClient.new()

    items = await c.search('защитные стекла на a53', 123585479)
    print(items)
    hist = await c.price_history(items[0].id)
    print(hist)


if __name__ == '__main__':
    asyncio.run(main())
