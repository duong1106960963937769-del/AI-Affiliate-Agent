from .base import NOT_CONFIRMED, ConnectorInfo, MarketplaceConnector, NotAvailableError


class UnverifiedConnector(MarketplaceConnector):
    """Khung connector cho sàn mà API chính thức CHƯA được xác minh. Mọi thao tác dữ liệu đều từ chối."""

    def _na(self):
        raise NotAvailableError(f"API {self.info.display_name} chưa được xác minh hoặc chưa được cấp quyền "
                                f"({self.info.availability}). Hệ thống không tạo dữ liệu giả.")

    def connect(self, **kwargs): self._na()
    def search_products(self, **filters): self._na()
    def get_product_details(self, product_id): self._na()
    def get_affiliate_products(self, **filters): self._na()
    def get_commission(self, product_id): self._na()
    def get_product_metrics(self, product_id): self._na()

    def disconnect(self) -> None:
        return None  # không có gì để ngắt; việc xóa token trong DB do service đảm nhiệm

    def get_connection_status(self) -> str:
        return "api_not_confirmed" if self.info.availability == NOT_CONFIRMED else "not_linked"
