from sqlalchemy.orm import Session

from ..models import ApiUsageLog


def log_api_call(db: Session, service: str, endpoint: str, *, success: bool, status_code: int | None = None,
                 error_code: str | None = None, latency_ms: int | None = None) -> None:
    """Ghi một lần gọi API ra bảng api_usage_logs (không ghi token hay nội dung)."""
    db.add(ApiUsageLog(service=service, endpoint=endpoint[:200], success=success, status_code=status_code,
                       error_code=error_code, latency_ms=latency_ms))
    db.commit()
