from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class WBPrices:
    basic: Decimal
    """Basic price (without discounts)."""
    total: Decimal
    """Total price (including discounts)."""

    def __init__(self, basic: int | Decimal, total: int | Decimal):
        self.basic = Decimal(basic / 100) if isinstance(basic, int) else basic
        self.total = Decimal(total / 100) if isinstance(total, int) else total

    @classmethod
    def from_dict(cls, data: dict) -> 'WBPrices':
        return cls(
            basic=data['basic'],
            total=data['total']
        )

@dataclass
class WBItemVariant:
    prices: WBPrices


@dataclass
class WBItem:
    id: int
    """WB id/articul of an item."""
    name: str = None
    variants: list[WBItemVariant] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> 'WBItem':
        return cls(
            id=data['id'],
            name=data['name'],
            variants=[
                WBItemVariant(
                    prices=WBPrices.from_dict(v['price'])
                ) for v in data['sizes']
            ]
        )
