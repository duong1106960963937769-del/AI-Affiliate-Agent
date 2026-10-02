from .base import NOT_CONFIRMED, ConnectorInfo
from .unverified import UnverifiedConnector


class TikTokShopConnector(UnverifiedConnector):
    info = ConnectorInfo(
        key="tiktok_shop", display_name="TikTok Shop", availability=NOT_CONFIRMED, auth_method="UNKNOWN",
        note="TikTok API access requires approval. TikTok Shop Vietnam API availability: NOT CONFIRMED. "
             "Cần xác minh Affiliate Seller/Partner/Creator API trên Partner Center trước khi triển khai OAuth.",
        doc_links=["https://partner.tiktokshop.com/"],
    )
