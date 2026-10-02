from .base import NOT_CONFIRMED, ConnectorInfo
from .unverified import UnverifiedConnector


class ShopeeConnector(UnverifiedConnector):
    info = ConnectorInfo(
        key="shopee", display_name="Shopee (Việt Nam)", availability=NOT_CONFIRMED, auth_method="UNKNOWN",
        note="Shopee Vietnam API availability: NOT CONFIRMED. Chưa đọc được tài liệu chính thức; "
             "cần xác minh Shopee Affiliate Open API (cách xác thực, quyền truy cập, giới hạn, chi phí) trước khi triển khai.",
        doc_links=["https://affiliate.shopee.vn/open_api/list"],
    )
