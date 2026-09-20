"""Live Govt (Agmarknet via data.gov.in) mandi price client.

Dataset: Current Daily Price of Various Commodities from Various Markets (Mandi)
Resource: 9ef84268-d588-465a-a308-a864a43d0070
Docs: https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi

Record fields (Rs/quintal wholesale):
  state, district, market, commodity, variety, grade,
  arrival_date (DD/MM/YYYY), min_price, max_price, modal_price
"""
import os
import time
import logging
from typing import List, Dict, Any, Optional

import requests

logger = logging.getLogger("gov_client")

RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
API_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

# Field names use lowercase ids (filters[commodity] works, filters[Commodity] returns 0)
FILTER_COMMODITY = "filters[commodity]"
FILTER_STATE = "filters[state]"

_session: Optional[requests.Session] = None


def _load_dotenv():
    """Minimal .env loader (no extra dependency)."""
    try:
        base = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(base, ".env")
        if not os.path.exists(env_path):
            return
        with open(env_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip("'").strip('"')
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception as e:
        logger.warning("dotenv load failed: %s", e)


_load_dotenv()


def get_api_key() -> Optional[str]:
    return (
        os.getenv("DATA_GOV_IN_API_KEY")
        or os.getenv("DATA_GOV_API_KEY")
        or os.getenv("AGMARKNET_API_KEY")
    )


def _session_singleton() -> requests.Session:
    global _session
    if _session is None:
        s = requests.Session()
        s.headers.update(
            {"User-Agent": "farmer_api/1.0 (+agmarknet via data.gov.in)", "Accept": "application/json"}
        )
        _session = s
    return _session


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None or v == "":
            return None
        return float(str(v).replace(",", "").strip())
    except (ValueError, TypeError, AttributeError):
        return None


def fetch_commodity_records(
    commodity: str,
    state: str = "",
    limit: int = 1000,
    max_records: int = 3000,
    timeout: int = 30,
) -> List[Dict[str, Any]]:
    """Fetch ALL records for one govt commodity (paginated). Raises on missing key / HTTP error."""
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("DATA_GOV_IN_API_KEY is not set")
    sess = _session_singleton()
    out: List[Dict[str, Any]] = []
    offset = 0
    total: Optional[int] = None
    attempts = 0
    while True:
        params: Dict[str, Any] = {
            "api-key": api_key,
            "format": "json",
            "offset": offset,
            "limit": min(limit, 1000),
            FILTER_COMMODITY: commodity,
        }
        if state:
            params[FILTER_STATE] = state
        try:
            r = sess.get(API_URL, params=params, timeout=timeout)
            r.raise_for_status()
            payload = r.json()
        except requests.RequestException as e:
            attempts += 1
            if attempts >= 3:
                raise
            logger.warning("retry %d for %s after %s", attempts, commodity, e)
            time.sleep(1.5 * attempts)
            continue
        attempts = 0
        if payload.get("status") != "ok":
            raise RuntimeError(f"Gov API error: {payload.get('message', payload)}")
        batch = payload.get("records") or []
        if total is None:
            try:
                total = int(payload.get("total", 0))
            except (ValueError, TypeError):
                total = 0
        if not batch:
            break
        out.extend(batch)
        offset += len(batch)
        if len(batch) < min(limit, 1000):
            break
        if total is not None and offset >= total:
            break
        if len(out) >= max_records:
            break
        time.sleep(0.2)  # polite between pages
    return out


def _latest_date(records: List[Dict[str, Any]]) -> Optional[str]:
    """Return latest arrival_date string (DD/MM/YYYY)."""
    from datetime import datetime

    best = None
    best_dt = None
    for r in records:
        s = (r.get("arrival_date") or "").strip()
        try:
            dt = datetime.strptime(s, "%d/%m/%Y")
        except (ValueError, TypeError, AttributeError):
            continue
        if best_dt is None or dt > best_dt:
            best_dt = dt
            best = s
    return best


def compute_national_average(records: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Average modal across all states/markets. Prices stay in Rs/quintal here.

    Robustness:
    - API filters[commodity] does substring/OR matching (Potato also returns
      Sweet Potato, Onion returns Onion Green, 'Raw Honey' returns Papaya(Raw)...).
      Caller exact-filters before calling; we defensively handle mixed input.
    - Drops obvious data-entry outliers (e.g. 0.02 Rs/quintal) via median band.
    """
    import statistics

    modals, mins, maxs = [], [], []
    for r in records:
        mo = _safe_float(r.get("modal_price"))
        mi = _safe_float(r.get("min_price"))
        ma = _safe_float(r.get("max_price"))
        if mo is not None and mo > 0:
            modals.append(mo)
        if mi is not None and mi > 0:
            mins.append(mi)
        if ma is not None and ma > 0:
            maxs.append(ma)
    if not modals:
        return None
    try:
        med = statistics.median(modals)
    except statistics.StatisticsError:
        return None
    # Keep values within [median/10, median*10] to drop entry errors like 0.02
    # while keeping real regional spread (350 vs 7000 for potato stays).
    lo, hi = (med / 10.0, med * 10.0) if med and med > 0 else (0, float("inf"))
    f_modals = [m for m in modals if lo <= m <= hi]
    f_mins = [m for m in mins if lo <= m <= hi]
    f_maxs = [m for m in maxs if lo <= m <= hi]
    if not f_modals:
        f_modals, f_mins, f_maxs = modals, mins, maxs
    return {
        "avg_modal_quintal": sum(f_modals) / len(f_modals),
        "min_quintal": min(f_mins) if f_mins else min(f_modals),
        "max_quintal": max(f_maxs) if f_maxs else max(f_modals),
        "markets_count": len(records),
        "arrival_date": _latest_date(records),
        "sample_state": records[0].get("state"),
        "sample_market": records[0].get("market"),
    }


def _exact_filter(records: List[Dict[str, Any]], commodity: str) -> List[Dict[str, Any]]:
    want = commodity.strip().lower()
    exact = [r for r in records if (r.get("commodity") or "").strip().lower() == want]
    return exact


def fetch_average_for_candidates(
    candidates: List[str], state: str = ""
) -> Optional[Dict[str, Any]]:
    """Try candidate govt commodities in order; return first with data.

    Exact-matches commodity client-side because the API does substring/OR
    matching. Returns dict with quintal prices + matched_commodity, or None.
    """
    for cand in candidates:
        if not cand:
            continue
        try:
            recs = fetch_commodity_records(cand, state=state)
        except Exception as e:
            logger.warning("fetch failed for %s: %s", cand, e)
            continue  # try next candidate; cache layer decides fallback
        if not recs:
            continue
        exact = _exact_filter(recs, cand)
        if not exact:
            # No exact series for this candidate (e.g. 'Raw Honey' matching
            # Papaya(Raw)) -> try next candidate, eventually static fallback.
            logger.info("no exact match for %s (%d substring rows ignored)", cand, len(recs))
            continue
        avg = compute_national_average(exact)
        if avg:
            avg["matched_commodity"] = cand.strip()
            return avg
    return None
