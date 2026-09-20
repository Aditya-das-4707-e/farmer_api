# Indian Market Price API

> **Live:** https://farmer-api-ooi2.onrender.com/ · Swagger UI: https://farmer-api-ooi2.onrender.com/docs

A lightweight FastAPI service that returns general Indian market prices (INR) for agricultural products. Search by product name — plural-tolerant — and get the market rate with Hindi and Bengali names.

Example: `GET https://farmer-api-ooi2.onrender.com/products/?name=rice` → market price(s) for rice varieties.

> Version 3.0.0 · Single-file app (`main.py`) · 411 curated products · No database required.
>
> **Data status: static snapshot.** Prices are currently hardcoded in `main.py` (indicative general market rates, not live mandi data). Real-time/dynamic price updates are planned for a future release.

## Features

- **Name search** — `GET /products/` with `?name=` query param.
- **Plural-tolerant matching** — `potato` / `potatos` / `potatoes` all match; same for `onion/onions`, `tomato/tomatoes`, `chilli/chillies`, etc.
- **Generic-term expansion** — `egg` → Poultry Egg + Duck Egg, `honey` → all honeys, `milk` → all milks, `mango` → all mangoes.
- **3-tier match strategy** — exact normalized match → whole-word match → substring fallback.
- **Trilingual names** — English `product_name` + `hindi_name` + `bengali_name`.
- **Formatted price** — `market_price` string like `"Rs 28 per kg"` auto-added per response.
- **Zero-config data** — in-memory list (`RAW_PRODUCTS`), auto IDs, Title-Cased names.
- **Auto docs** — Swagger UI at `/docs`, ReDoc at `/redoc`.

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | FastAPI 0.101.0 |
| Server | Uvicorn 0.23.2 |
| Validation | Pydantic 2.4.2 |
| Language | Python 3.12 (see `.python-version`; 3.8+ should work) |
| Storage | In-memory Python list (no DB) — static for now, dynamic/real-time data planned |
| Hosting | Render — live at https://farmer-api-ooi2.onrender.com/ |

See `requirements.txt`.

## Live Deployment

- **Base URL:** https://farmer-api-ooi2.onrender.com/
- **Swagger UI:** https://farmer-api-ooi2.onrender.com/docs
- **ReDoc:** https://farmer-api-ooi2.onrender.com/redoc
- **Health check:** just open the base URL (FastAPI root) or hit the example below.

Try it now (no setup needed):

```bash
curl "https://farmer-api-ooi2.onrender.com/products/?name=potato"
curl "https://farmer-api-ooi2.onrender.com/products/?name=honey"
curl "https://farmer-api-ooi2.onrender.com/products/?name=egg"
```

> Note: Render free-tier instances may cold-start (first request can take ~30–60s), then respond normally.

## Project Structure

```
farmer_api/
├── main.py            # App, data (RAW_PRODUCTS), search logic, route
├── requirements.txt   # fastapi, uvicorn, pydantic (pinned)
├── README.md          # This file
├── .python-version    # Python 3.12
├── .gitignore         # ignores /env, /__pycache__
├── env/               # Local virtualenv (ignored, not committed)
└── __pycache__/       # Bytecode cache (ignored)
```

## Getting Started (Local Development)

Live API above is ready to use — the steps below are only for running/modifying it locally.

### 1. Prerequisites

- Python 3.8+ (`python3 --version`)

### 2. Clone & install

```bash
git clone <your-repo-url>
cd farmer_api

python3 -m venv env
source env/bin/activate        # Windows: env\Scripts\activate

pip install -r requirements.txt
```

### 3. Run

```bash
uvicorn main:app --reload
```

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

Custom host/port:

```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

## API Reference

### `GET /products/`

Search products by name.

| Param | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Product name. Plural-tolerant, case-insensitive. Generic terms return multiple items. |

**Success:** `200 OK` — JSON array of `ProductPrice`.
**Not found:** `404` — `{"detail": "No product found with name '<name>'"}`.
**Missing param:** `422` — FastAPI validation error.

#### Response schema (`ProductPrice`)

```json
{
  "id": 10,
  "product_name": "Potato",
  "hindi_name": "आलू",
  "bengali_name": "আলু",
  "market_price_per_kg": 28.0,
  "unit": "kg",
  "currency": "INR",
  "market_price": "Rs 28 per kg"
}
```

| Field | Type | Notes |
|---|---|---|
| `id` | int | Auto index (1-based, curated order) |
| `product_name` | string | Title-Cased English name |
| `hindi_name` | string \| null | Hindi name (Devanagari) |
| `bengali_name` | string \| null | Bengali name |
| `market_price_per_kg` | float | Numeric price (despite name, value is per `unit`) |
| `unit` | string | `kg` (default), `litre`, or `piece` |
| `currency` | string | Always `INR` |
| `market_price` | string \| null | Formatted `"Rs <price> per <unit>"`, set at request time |

### Examples

Live examples (swap the base URL with `http://127.0.0.1:8000` for local):

```bash
curl "https://farmer-api-ooi2.onrender.com/products/?name=potato"
curl "https://farmer-api-ooi2.onrender.com/products/?name=potatoes"  # same result
curl "https://farmer-api-ooi2.onrender.com/products/?name=RICE"
```

Exact match (local):

```bash
curl "http://127.0.0.1:8000/products/?name=potato"
curl "http://127.0.0.1:8000/products/?name=potatoes"  # same result
curl "http://127.0.0.1:8000/products/?name=RICE"
```

```json
[
  {
    "id": 10,
    "product_name": "Potato",
    "hindi_name": "आलू",
    "bengali_name": "আলু",
    "market_price_per_kg": 28.0,
    "unit": "kg",
    "currency": "INR",
    "market_price": "Rs 28 per kg"
  }
]
```

Generic term (multiple results, live):

```bash
curl "https://farmer-api-ooi2.onrender.com/products/?name=egg"
curl "https://farmer-api-ooi2.onrender.com/products/?name=honey"
curl "https://farmer-api-ooi2.onrender.com/products/?name=milk"
```

Local equivalents:

```bash
curl "http://127.0.0.1:8000/products/?name=egg"
curl "http://127.0.0.1:8000/products/?name=honey"
curl "http://127.0.0.1:8000/products/?name=milk"
```

```bash
# 404 example
curl "http://127.0.0.1:8000/products/?name=xyz123"
# {"detail":"No product found with name 'xyz123'"}
```

Python example:

```python
import requests
r = requests.get("http://127.0.0.1:8000/products/", params={"name": "onions"})
print(r.json())
```

## How Search Works

`main.py:458-523` — all logic in `normalize_word()` / `normalize_name()` / `find_all_by_product()`.

1. **Normalization** — lowercase, strip punctuation, collapse whitespace, then per-word plural stripping:
   - `ies → i` (`chillies → chilli`), `oes → drop -es` (`potatoes → potato`, `mangoes → mango`), `ches/shes/sses/xes/zes → drop -es` (`peaches → peach`), trailing `s → drop` (`onions → onion`, typo `potatos → potato`), `leaves → leaf`, trailing `y → i` (`chilly → chilli`).
2. **Tier 1 – exact normalized match** → single item (e.g. `raw honey` → Raw Honey).
3. **Tier 2 – whole-word match** → every query word appears as a whole word in the product (e.g. `honey` → all honeys, `milk` → all milks, not Milky Mushroom). Sorted by fewest extra words, then curated `id`.
4. **Tier 3 – substring fallback** → `key in norm or norm in key`.

Precomputed index: `_normalized_index` (dict) + `_normalized_list` (list) at import time.

## Data Coverage (Static Snapshot — Dynamic Planned)

411 entries in `RAW_PRODUCTS` (`main.py:28-440`), each `(name, hindi, bengali, price, unit)`. **Current status: static/hardcoded indicative general market rates in INR — not live mandi prices.** Real-time data ingestion (with date/region/mandi breakdown) is planned; the API contract (`ProductPrice` shape) is intended to stay compatible when that lands.

Categories: cereals & millets (rice varieties, wheat, maize, jowar, bajra, ragi…), pulses & dals, vegetables & greens, mushrooms, fruits (mango/banana/orange/grape variants…), oilseeds, fibres (cotton, jute), plantation (tea, coffee, cocoa, rubber, areca, cashew, tobacco), spices (turmeric → saffron), medicinal/aromatic plants, flowers, dairy/poultry/meat/fish/seafood, honey & bee products, silk cocoons, and value-added goods (jaggery, flour, oils, ghee, paneer, pickles, juices, papad…).

Units: mostly `kg`; milk/oils/buttermilk in `litre`; eggs, cow-dung cake, soap in `piece`.

Price range: ~Rs 4 (sugarcane/kg) to Rs 2,50,000 (saffron/kg).

## Configuration & Deployment

- Live on Render: https://farmer-api-ooi2.onrender.com/ (auto-deploys from the connected repo/branch).
- No env vars, no DB, no auth — runs as-is.
- Prices are currently hardcoded; to update, edit `RAW_PRODUCTS` in `main.py`, commit/push (Render redeploys), or restart locally.
- Production run: `uvicorn main:app --host 0.0.0.0 --port 8000` (add `--workers 4` as needed, or put behind nginx/Docker).
- Render start command (if configuring manually): `uvicorn main:app --host 0.0.0.0 --port $PORT`.

## Limitations (Current Static Version)

- Static prices — no live update yet, no date/region/mandi breakdown (real-time/dynamic data is the planned next step).
- Single search-only endpoint; no create/update/delete, pagination, or filters.
- `market_price_per_kg` field name is legacy — value is actually per `unit` (kg/litre/piece).
- Whole-word matching is English-only; Hindi/Bengali names are returned but not searchable.
- `ies → i` normalization can over-stem (e.g. `strawberries → strawberri`), still consistent on both sides so matches work.

## Roadmap

- [ ] **Dynamic real-time prices** — replace hardcoded `RAW_PRODUCTS` with a live data source (mandi/API/scraper + scheduled refresh), adding date/region/mandi fields while keeping the current response shape backward-compatible.
- Search by Hindi/Bengali name.
- Query filters (`unit`, price range, category) + pagination.
- Move data to SQLite/Postgres or JSON/CSV + admin CRUD.
- Live price ingestion / per-mandi rates (see top roadmap item).
- Tests (`pytest` + `httpx`/`TestClient`) and Dockerfile.

## License

No license file yet. Add one (e.g. MIT) if you plan to publish.
