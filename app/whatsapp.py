"""WAHA (WhatsApp HTTP API) client - posts to WhatsApp *Status* (Stories)."""
import base64
import logging

from . import config
from .http_util import session

log = logging.getLogger("waha")


def _headers() -> dict:
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if config.WAHA_API_KEY:
        h["X-Api-Key"] = config.WAHA_API_KEY
    return h


def session_status() -> str:
    r = session.get(f"{config.WAHA_BASE_URL}/api/sessions/{config.WAHA_SESSION}", headers=_headers(), timeout=20)
    if r.status_code == 404:
        return "NOT_FOUND"
    r.raise_for_status()
    return r.json().get("status", "UNKNOWN")


def ensure_session() -> None:
    """Starts the session if needed. First time: scan the QR at {WAHA_BASE_URL}/dashboard."""
    status = session_status()
    if status == "NOT_FOUND":
        session.post(f"{config.WAHA_BASE_URL}/api/sessions/start", headers=_headers(), json={"name": config.WAHA_SESSION}, timeout=30)
        status = session_status()
    if status == "STOPPED":
        session.post(f"{config.WAHA_BASE_URL}/api/sessions/{config.WAHA_SESSION}/start", headers=_headers(), timeout=30)
        status = session_status()
    if status != "WORKING":
        raise RuntimeError(
            f"WAHA session '{config.WAHA_SESSION}' is {status}. Open {config.WAHA_BASE_URL}/dashboard and scan the QR with your SECONDARY WhatsApp number."
        )


def post_status_image(jpeg: bytes, caption: str) -> dict:
    payload = {
        "file": {"mimetype": "image/jpeg", "filename": "product-of-the-day.jpg", "data": base64.b64encode(jpeg).decode()},
        "caption": caption,
    }
    r = session.post(f"{config.WAHA_BASE_URL}/api/{config.WAHA_SESSION}/status/image", headers=_headers(), json=payload, timeout=90)
    if not r.ok:
        raise RuntimeError(f"WAHA status/image failed {r.status_code}: {r.text[:300]}")
    return r.json() if r.content else {}
