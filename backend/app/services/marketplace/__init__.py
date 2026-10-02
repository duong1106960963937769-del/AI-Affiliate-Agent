from .base import MarketplaceConnector, NotAvailableError
from .shopee import ShopeeConnector
from .tiktok import TikTokShopConnector

REGISTRY: dict[str, MarketplaceConnector] = {c.info.key: c for c in (TikTokShopConnector(), ShopeeConnector())}


def get_connector(key: str) -> MarketplaceConnector:
    if key not in REGISTRY:
        raise KeyError(key)
    return REGISTRY[key]


__all__ = ["REGISTRY", "get_connector", "MarketplaceConnector", "NotAvailableError"]
