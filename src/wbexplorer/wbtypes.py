from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class WBPrices:
    basic: Decimal | None = None
    """Basic price (without discounts)."""
    total: Decimal | None = None
    """Total price (including discounts)."""

    def __init__(self, basic: int | Decimal | None, total: int | Decimal | None):
        self.basic = Decimal(basic / 100) if isinstance(basic, int) else basic
        self.total = Decimal(total / 100) if isinstance(total, int) else total

    @classmethod
    def from_dict(cls, data: dict) -> 'WBPrices':
        return cls(
            basic=data.get('basic'),
            total=data.get('total')
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
                    prices=WBPrices.from_dict(v.get('price') or {})
                ) for v in data['sizes']
            ]
        )
