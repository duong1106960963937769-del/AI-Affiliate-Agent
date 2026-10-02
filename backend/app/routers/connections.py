import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import MarketplaceConnection, User, utcnow
from ..services.marketplace import REGISTRY, NotAvailableError, get_connector

router = APIRouter(prefix="/connections", tags=["connections"])
log = logging.getLogger("app")

LABELS = {
    "not_linked": "Chưa liên kết",
    "api_not_confirmed": "API chưa được xác minh / chưa cấp quyền",
    "connected": "Đã kết nối",
    "expired": "Cần kết nối lại",
    "error": "Cần kết nối lại",
}


def _user_id(db: Session) -> int:
    u = db.query(User).filter_by(username="local").first()
    if not u:
        u = User(username="local", display_name="Người dùng cục bộ")
        db.add(u)
        db.commit()
    return u.id


def _row(db: Session, key: str):
    return db.query(MarketplaceConnection).filter_by(user_id=_user_id(db), marketplace=key).first()


def _view(db: Session, key: str) -> dict:
    c = get_connector(key)
    row = _row(db, key)
    status = row.connection_status if row and row.connection_status == "connected" else c.get_connection_status()
    if row and row.connection_status in ("expired", "error"):
        status = row.connection_status
    connected = status == "connected"
    return {
        "marketplace": key, "name": c.info.display_name, "status": status, "status_label": LABELS.get(status, status),
        "availability": c.info.availability, "auth_method": c.info.auth_method, "is_free": c.info.is_free,
        "requires_approval": c.info.requires_approval, "note": c.info.note, "doc_links": c.info.doc_links,
        "last_sync_at": row.last_sync_at.isoformat() if row and row.last_sync_at else None,
        "can_connect": False,  # chỉ bật khi connector được xác minh và triển khai
        "can_disconnect": connected, "can_refresh": connected,
    }


@router.get("")
def list_connections(db: Session = Depends(get_db)):
    return [_view(db, k) for k in REGISTRY]


def _get(key: str):
    try:
        return get_connector(key)
    except KeyError:
        raise HTTPException(404, "Marketplace không được hỗ trợ.")


@router.post("/{key}/connect")
def connect(key: str, db: Session = Depends(get_db)):
    c = _get(key)
    try:
        c.connect()
    except NotAvailableError as e:
        log.warning("connect refused marketplace=%s availability=%s", key, c.info.availability)
        raise HTTPException(501, e.user_message)
    return _view(db, key)


@router.post("/{key}/refresh")
def refresh(key: str, db: Session = Depends(get_db)):
    c = _get(key)
    if _view(db, key)["status"] != "connected":
        raise HTTPException(409, "Chưa có kết nối để làm mới. Hãy kết nối trước.")
    raise HTTPException(501, f"Làm mới kết nối {c.info.display_name} chưa được triển khai.")


@router.post("/{key}/disconnect")
def disconnect(key: str, db: Session = Depends(get_db)):
    c = _get(key)
    c.disconnect()
    row = _row(db, key)
    if row:  # xóa token đã lưu
        row.access_token_encrypted = row.refresh_token_encrypted = row.token_expires_at = None
        row.connection_status, row.updated_at = "not_linked", utcnow()
        db.commit()
    return _view(db, key)
