"""TTL in-memory cache for govt price averages. Keyed by govt commodity (+state)."""
import time
import threading
from typing import Dict, Any, Optional

CACHE_TTL_SECONDS = 6 * 60 * 60  # 6 hours (mandi data is daily)

_lock = threading.Lock()
_store: Dict[str, Dict[str, Any]] = {}


def _key(commodity: str, state: str = "") -> str:
    return f"{commodity.strip().lower()}||{state.strip().lower()}"


def get(commodity: str, state: str = "") -> Optional[Dict[str, Any]]:
    k = _key(commodity, state)
    with _lock:
        e = _store.get(k)
        if not e:
            return None
        if time.time() - e["fetched_at"] > CACHE_TTL_SECONDS:
            del _store[k]
            return None
        return dict(e["data"])


def set(commodity: str, state: str, data: Dict[str, Any]) -> None:
    k = _key(commodity, state)
    with _lock:
        _store[k] = {"fetched_at": time.time(), "data": dict(data)}


def get_by_product_cache_key(product_key: str, state: str = "") -> Optional[Dict[str, Any]]:
    """Cache for fully-resolved product averages (optional layer)."""
    return get(f"product::{product_key}", state)


def set_by_product_cache_key(product_key: str, state: str, data: Dict[str, Any]) -> None:
    set(f"product::{product_key}", state, data)


def clear() -> int:
    with _lock:
        n = len(_store)
        _store.clear()
        return n


def stats() -> Dict[str, Any]:
    with _lock:
        return {"entries": len(_store), "ttl_seconds": CACHE_TTL_SECONDS}
