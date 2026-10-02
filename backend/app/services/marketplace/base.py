"""Giao diện MarketplaceConnector. Mỗi sàn một connector riêng; thêm sàn mới không phải sửa hệ thống.

QUY TẮC: connector chỉ gọi API/ủy quyền CHÍNH THỨC đã được xác minh. Khi chưa xác minh hoặc chưa được cấp
quyền, các hàm ném NotAvailableError — tuyệt đối không trả dữ liệu giả.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

# Mức xác minh API
NOT_CONFIRMED = "NOT_CONFIRMED"
REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
CONFIRMED = "CONFIRMED"


class NotAvailableError(Exception):
    def __init__(self, user_message: str):
        super().__init__(user_message)
        self.user_message = user_message


@dataclass
class ConnectorInfo:
    key: str
    display_name: str
    availability: str                      # NOT_CONFIRMED | REQUIRES_APPROVAL | CONFIRMED
    auth_method: str                       # "UNKNOWN" | "oauth" | "api_key_signature" ...
    is_free: str = "UNKNOWN"               # Confirmed | Unknown | Paid
    requires_approval: str = "UNKNOWN"     # Yes | No | Unknown
    note: str = ""
    doc_links: list[str] = field(default_factory=list)


class MarketplaceConnector(ABC):
    info: ConnectorInfo

    @abstractmethod
    def connect(self, **kwargs) -> dict: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def get_connection_status(self) -> str: ...

    @abstractmethod
    def search_products(self, **filters) -> list[dict]: ...

    @abstractmethod
    def get_product_details(self, product_id: str) -> dict: ...

    @abstractmethod
    def get_affiliate_products(self, **filters) -> list[dict]: ...

    @abstractmethod
    def get_commission(self, product_id: str) -> dict: ...

    @abstractmethod
    def get_product_metrics(self, product_id: str) -> dict: ...
